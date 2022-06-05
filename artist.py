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
from model import Artist, db, Show,  Venue
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
        data = []
        artists = Artist.query.filter(
            Artist.name.ilike(f'%{partial_name}%')).all()
        count = len(artists)

        if count > 0:

            for artist in artists:
                data.append({
                    "id": artist.id,
                    "name": artist.name,
                    "num_upcoming_shows": len(artist.shows)
                })

            response = {
                "count": count,
                "data": data
            }

    except BaseException:
        flash(
            f'An error occured, could not search with {partial_name} was not successfully!')
        print(sys.exc_info())

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

        upcoming_shows = []
        past_shows = []
        all_shows = db.session.query(Venue, Show).join(Show).filter(Show.artist_id == artist_id).all()

        for venue, show in all_shows:
            if datetime.date(show.start_time) >= date.today():
                upcoming_shows.append({
                    "venue_id": venue.id,
                    "venue_name": venue.name,
                    "venue_image_link": venue.image_link,
                    "start_time": show.start_time
                })
            else:
                past_shows.append({
                    "venue_id": venue.id,
                    "venue_name": venue.name,
                    "venue_image_link": venue.image_link,
                    "start_time": show.start_time
                })

        data['past_shows'] = past_shows
        data['past_shows_count'] = len(past_shows)  

        data['upcoming_shows'] = upcoming_shows
        data['upcoming_shows_count'] = len(upcoming_shows)
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
    if form.validate_on_submit():
            print("Form Valid")
    else:
            return render_template(
                'forms/edit_artist.html', form=form, artist=artist)

    try:
        artist = Artist.query.get(artist_id)

        existing_artist = Artist.query.filter(
            Artist.name.ilike(f'%{form.name.data}%')).all()
        if len(existing_artist) > 0 and form.name.data.lower(
        ) != artist.name.lower():
            print(form.name.data.lower(), artist.name.lower())
            form.name.errors.append('Artist name ' + request.form['name'] + ' already exists!')
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

        if form.validate_on_submit():
            print("Form Valid")
        else:
            return render_template('forms/new_artist.html', form=form)

        existing_artist = Artist.query.filter(
            Artist.name.ilike(f'%{form.name.data}%')).all()
        if len(existing_artist) > 0:
            form.name.errors.append('Artist name ' + request.form['name'] + ' already exists!')
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

    return redirect(
        url_for('index'))


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
