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
from model import Artist, db
import sys
import psycopg2
from forms import *
from config import DatabaseURI

artist_blueprint = Blueprint('artist_blueprint', __name__)
#  Artists
#  ----------------------------------------------------------------


@artist_blueprint.route('/artists')
def artists():
    try:
        data = []
        artists = Artist.query.all()

        data = [{
            "id": item.id,
            "name": item.name,
        } for item in artists]

        if len(data) > 0:
            flash('Artists successfully listed!')
    except BaseException:
        flash('Artists was successfully listed!')
        print(sys.exc_info())

    return render_template('pages/artists.html', artists=data)


@artist_blueprint.route('/artists/search', methods=['POST'])
def search_artists():
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    try:
        partial_name = request.form.get('search_term', '')
        response = {}
        artists = Artist.query.filter(
            Artist.name.ilike(f'%{partial_name}%')).all()
        count = len(artists)

        if count > 0:

            if count > 1:
                list_of_ids = ",".join([str(item.id) for item in artists])
            elif count == 1:
                list_of_ids = str(artists[0].id)

            connection = psycopg2.connect(
                DatabaseURI.SQLALCHEMY_DATABASE_URI)
            cursor = connection.cursor()

            cursor.execute(f'''
        select a.id, count(a.id)
        from "Artists" a join show_items s on a.id = s.artist_id where s.artist_id in ({list_of_ids}) and s.start_time >= '{date.today()}'
        group by a.id
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
                } for item in artists]
            }

    except BaseException:
        flash(
            f'An error occured, could not search with {partial_name} was not successfully!')
        print(sys.exc_info())
    finally:
        connection.close()

    return render_template('pages/search_artists.html',
                           results=response, search_term=partial_name)


@artist_blueprint.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    try:
        connection = psycopg2.connect(DatabaseURI.SQLALCHEMY_DATABASE_URI)
        cursor = connection.cursor()
        data = {}
        artist = Artist.query.get(artist_id)

        data = {
            "id": artist.id,
            "name": artist.name,
            "genres": artist.genres.split(','),
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "website": artist.website_link,
            "facebook_link": artist.facebook_link,
            "seeking_venue": artist.is_venue_seeking,
            "seeking_description": artist.venue_seeking_description,
            "image_link": artist.image_link,
        }

        cursor.execute(f'''
      select v.id, v.name, v.image_link, s.start_time
      from "Venues" v join show_items s on v.id = s.venue_id where s.artist_id = {artist_id} and s.start_time < '{date.today()}'
      ''')

        past_shows = cursor.fetchall()
        data['past_shows'] = [{"venue_id": id,
                               "venue_name": name,
                               "venue_image_link": image_link,
                               "start_time": start_time} for id, name, image_link, start_time in past_shows]
        data['past_shows_count'] = len(data['past_shows'])

        cursor.execute(f'''
      select v.id, v.name, v.image_link, s.start_time
      from "Venues" v join show_items s on v.id = s.venue_id where s.artist_id = {artist_id} and s.start_time >= '{date.today()}'
      ''')

        upcoming_shows = cursor.fetchall()
        print('upcoming_shows', upcoming_shows)
        data['upcoming_shows'] = [{"venue_id": id,
                                   "venue_name": name,
                                   "venue_image_link": image_link,
                                   "start_time": start_time} for id, name, image_link, start_time in upcoming_shows]
        data['upcoming_shows_count'] = len(data['upcoming_shows'])
        print('data', data)
    except BaseException:
        flash(f'Details for venue: {artist_id} was not successfully fetched!')
        print(sys.exc_info())
    finally:
        connection.close()

    return render_template('pages/show_artist.html', artist=data)


@artist_blueprint.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    try:
        artist = Artist.query.get(artist_id)

        form.name.data = artist.name
        form.city.data = artist.city
        form.state.data = artist.state
        form.phone.data = artist.phone
        form.genres.data = artist.genres.split(',')
        form.image_link.data = artist.image_link
        form.facebook_link.data = artist.facebook_link
        form.website_link.data = artist.website_link
        form.seeking_venue.data = artist.is_venue_seeking
        form.seeking_description.data = artist.venue_seeking_description

    except BaseException:
        flash(f'Artist: {artist_id} was not successfully loaded!')
        print(sys.exc_info())

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@artist_blueprint.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()
    try:
        artist = Artist.query.get(artist_id)

        existing_artist = Artist.query.filter(
            Artist.name.ilike(f'%{form.name.data}%')).all()
        if len(existing_artist) > 0 and form.name.data.lower(
        ) != artist.name.lower():
            print(form.name.data.lower(), artist.name.lower())
            flash('Artist ' + request.form['name'] + ' already exists!')
            return render_template(
                'forms/edit_artist.html', form=form, artist=artist)

        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = ",".join(form.genres.data)
        artist.image_link = form.image_link.data
        artist.facebook_link = form.facebook_link.data
        artist.website_link = form.website_link.data
        artist.is_venue_seeking = form.seeking_venue.data
        artist.venue_seeking_description = form.seeking_description.data

        db.session.commit()
        flash(f'Artist: {artist_id} was successfully edited!')
    except BaseException:
        flash(f'Artist: {artist_id} was not successfully edited!')
        print(sys.exc_info())
        db.session.rollback()
    finally:
        db.session.close()

    # artist record with ID <artist_id> using the new attributes

    return redirect(
        url_for('artist_blueprint.show_artist', artist_id=artist_id))


@artist_blueprint.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@artist_blueprint.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    try:
        form = ArtistForm()

        existing_artist = Artist.query.filter(
            Artist.name.ilike(f'%{form.name.data}%')).all()
        if len(existing_artist) > 0:
            flash('Artist ' + request.form['name'] + ' already exists!')
            return render_template('forms/new_artist.html', form=form)

        genres = ",".join(form.genres.data)

        artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data, phone=form.phone.data, genres=genres,
                        image_link=form.image_link.data, facebook_link=form.facebook_link.data, website_link=form.website_link.data, is_venue_seeking=form.seeking_venue.data,
                        venue_seeking_description=form.seeking_description.data)

        db.session.add(artist)
        db.session.commit()

        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except BaseException:
        # e.g., flash('An error occurred. Artist ' + data.name + ' could not be
        # listed.')
        db.session.rollback()
        flash(
            'An error occured Artist ' +
            request.form['name'] +
            ' was not successfully listed!')
        print(sys.exc_info())
    finally:
        db.session.close()

    return render_template('pages/home.html')


@artist_blueprint.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit
    # could fail.
    try:
        artist = Artist.query.get(artist_id)
        db.session.delete(artist)
        db.session.commit()
        flash(f'Artist: {artist_id} was successfully deleted!')
    except BaseException:
        flash(f'Artist: {artist_id} was not successfully deleted!')
        print(sys.exc_info())
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'Success': True})
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the
    # homepage
