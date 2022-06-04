from flask import (
    Blueprint,
    jsonify, 
    render_template,
    request,
    flash,
    redirect,
    url_for
)
from datetime import date
from model import Venue, db
import sys
import psycopg2
from forms import *
from config import DatabaseURI

venue_blueprint = Blueprint('venue_blueprint', __name__)

#  Venues
#  ----------------------------------------------------------------

@venue_blueprint.route('/venues')
def venues():
    # num_upcoming_shows should be aggregated based on number of upcoming
    # shows per venue.
    try:
        connection = psycopg2.connect(DatabaseURI.SQLALCHEMY_DATABASE_URI)
        cursor = connection.cursor()

        cursor.execute(f'''
      select v.city, v.state, v.name, v.id, count(v.id)
      from "Venues" v left join show_items s on v.id = s.venue_id
      group by v.city, v.state, v.name, v.id
      ''')

        venues_data = cursor.fetchall()

        data = []
        results = {}

        for city, state, name, id, show_count in venues_data:
            location = (city, state)
            if location not in results:
                results[location] = []
            results[location].append(
                {"id": id, "name": name, "num_upcoming_shows": show_count})
        for key, value in results.items():
            data.append(
                {"city": key[0],
                 "state": key[1],
                 "venues": [{"id": show['id'], "name": show['name'], "num_upcoming_shows": show['num_upcoming_shows']} for show in value]
                 })
    except BaseException:
        flash('An error occured venues was not successfully listed!')
        print(sys.exc_info())
    finally:
        connection.close()

    return render_template('pages/venues.html', areas=data)


@venue_blueprint.route('/venues/search', methods=['POST'])
def search_venues():
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live
    # Music & Coffee"
    try:
        partial_name = request.form.get('search_term', '')
        response = {}
        venues = Venue.query.filter(
            Venue.name.ilike(f'%{partial_name}%')).all()
        count = len(venues)

        if count > 0:

            if count > 1:
                list_of_ids = ",".join([str(item.id) for item in venues])
            elif count == 1:
                list_of_ids = str(venues[0].id)

            connection = psycopg2.connect(
                DatabaseURI.SQLALCHEMY_DATABASE_URI)
            cursor = connection.cursor()

            cursor.execute(f'''
        select v.id, count(v.id)
        from "Venues" v join show_items s on v.id = s.venue_id where s.venue_id in ({list_of_ids}) and s.start_time >= '{date.today()}'
        group by v.id
        ''')

            show_count = cursor.fetchall()

            dict = {}

            for id, count in show_count:
                dict[id] = count

            response = {
                "count": count,
                "data": [{
                    "id": item.id,
                    "name": item.name,
                    "num_upcoming_shows": dict[item.id] if item.id in dict else 0
                } for item in venues]
            }

    except BaseException:
        flash(
            f'An error occured, could not search with {partial_name} was not successfully!')
        print(sys.exc_info())
    finally:
        connection.close()

    return render_template('pages/search_venues.html',
                           results=response, search_term=partial_name)


@venue_blueprint.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    try:
        connection = psycopg2.connect(DatabaseURI.SQLALCHEMY_DATABASE_URI)
        cursor = connection.cursor()
        data = {}
        venue = Venue.query.get(venue_id)

        data = {
            "id": venue.id,
            "name": venue.name,
            "genres": venue.genres.split(','),
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "website": venue.website_link,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.is_talent_seeking,
            "seeking_description": venue.talent_seeking_description,
            "image_link": venue.image_link
        }

        cursor.execute(f'''
      select a.id, a.name, a.image_link, s.start_time
      from "Artists" a join show_items s on a.id = s.artist_id where s.venue_id = {venue_id} and s.start_time < '{date.today()}'
      ''')

        past_shows = cursor.fetchall()
        data['past_shows'] = [{"artist_id": id,
                               "artist_name": name,
                               "artist_image_link": image_link,
                               "start_time": start_time} for id, name, image_link, start_time in past_shows]
        data['past_shows_count'] = len(data['past_shows'])

        cursor.execute(f'''
      select a.id, a.name, a.image_link, s.start_time
      from "Artists" a join show_items s on a.id = s.artist_id where s.venue_id = {venue_id} and s.start_time >= '{date.today()}'
      ''')

        upcoming_shows = cursor.fetchall()
        print('upcoming_shows', upcoming_shows)
        data['upcoming_shows'] = [{"artist_id": id,
                                   "artist_name": name,
                                   "artist_image_link": image_link,
                                   "start_time": start_time} for id, name, image_link, start_time in upcoming_shows]
        data['upcoming_shows_count'] = len(data['upcoming_shows'])
        print('data', data)
    except BaseException:
        flash(f'Details for venue: {venue_id} was not successfully fetched!')
        print(sys.exc_info())
    finally:
        connection.close()

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@venue_blueprint.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@venue_blueprint.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        form = VenueForm()

        existing_venue = Venue.query.filter(
            Venue.name.ilike(f'%{form.name.data}%')).all()
        if len(existing_venue) > 0:
            flash('Venue ' + request.form['name'] + ' already exists!')
            return render_template('forms/new_venue.html', form=form)

        genres = ",".join(form.genres.data)

        venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data, address=form.address.data, phone=form.phone.data, genres=genres,
                      image_link=form.image_link.data, facebook_link=form.facebook_link.data, website_link=form.website_link.data, is_talent_seeking=form.seeking_talent.data,
                      talent_seeking_description=form.seeking_description.data)

        db.session.add(venue)
        db.session.commit()

        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully created!')
    except BaseException:
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/ for flash messages
        db.session.rollback()
        flash(
            'An error occured Venue ' +
            request.form['name'] +
            ' was not successfully created!')
        print(sys.exc_info())
    finally:
        db.session.close()
    return render_template('pages/home.html')



@venue_blueprint.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit
    # could fail.
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash(f'Venue: {venue_id} was successfully deleted!')
    except BaseException:
        flash(f'Venue: {venue_id} was not successfully deleted!')
        print(sys.exc_info())
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'Success': True})


#  Update
#  ----------------------------------------------------------------




@venue_blueprint.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    try:
        venue = Venue.query.get(venue_id)

        form.name.id = venue.name
        form.genres.data = venue.genres.split(',')
        form.address.data = venue.address
        form.city.data = venue.city
        form.state.data = venue.state
        form.phone.data = venue.phone
        form.website_link.data = venue.website_link
        form.facebook_link.data = venue.facebook_link
        form.seeking_talent.data = venue.is_talent_seeking
        form.seeking_description.data = venue.talent_seeking_description
        form.image_link.data = venue.image_link
    except BaseException:
        flash(f'Venue: {venue_id} was not successfully loaded!')
        print(sys.exc_info())
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@venue_blueprint.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        form = VenueForm()

        existing_venue = Venue.query.filter(
            Venue.name.ilike(f'%{form.name.data}%')).all()
        if len(existing_venue) > 0 and form.name.data.lower() != venue.name.lower():
            print(form.name.data.lower(), venue.name.lower())
            flash('Venue ' + request.form['name'] + ' already exists!')
            return render_template(
                'forms/edit_venue.html', form=form, venue=venue)

        genres = ",".join(form.genres.data)

        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.genres = genres
        venue.image_link = form.image_link.data
        venue.facebook_link = form.facebook_link.data
        venue.website_link = form.website_link.data
        venue.is_talent_seeking = form.seeking_talent.data
        venue.talent_seeking_description = form.seeking_description.data

        db.session.commit()
        flash(f'Venue: {venue_id} was successfully edited!')
    except BaseException:
        flash(f'Venue: {venue_id} was not successfully edited!')
        print(sys.exc_info())
        db.session.rollback()
    finally:
        db.session.close()
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for('show_venue', venue_id=venue_id))