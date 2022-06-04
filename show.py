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
from model import Artist, Venue

show_blueprint = Blueprint('show_blueprint', __name__)


#  Shows
#  ----------------------------------------------------------------

@show_blueprint.route('/shows')
def shows():
    # displays list of shows at /shows
    try:
        data = []

        connection = psycopg2.connect(DatabaseURI.SQLALCHEMY_DATABASE_URI)
        cursor = connection.cursor()

        cursor.execute(f'''
      select v.id, v.name, a.id, a.name, a.image_link, s.start_time
      from show_items s join "Venues" v on  s.venue_id = v.id join "Artists" a on s.artist_id = a.id
      ''')

        show_data = cursor.fetchall()

        data = [{
            "venue_id": venue_id,
            "venue_name": venue_name,
            "artist_id": artist_id,
            "artist_name": artist_name,
            "artist_image_link": image_link,
            "start_time": start_time
        } for venue_id, venue_name, artist_id, artist_name, image_link, start_time in show_data]

        print('data', data)
    except BaseException:
        flash(f'An error occured, could not get all shows successfully!')
        print(sys.exc_info())
    finally:
        connection.close()

    return render_template('pages/shows.html', shows=data)


@show_blueprint.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()

    venues = Venue.query.all()
    artists = Artist.query.all()

    form.artist_id.choices = []
    form.venue_id.choices = []

    for venue in venues:
        form.venue_id.choices.append((venue.id, venue.name))

    for artist in artists:
        form.artist_id.choices.append((artist.id, artist.name))

    return render_template('forms/new_show.html', form=form)


@show_blueprint.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing
    # form
    try:
        form = ShowForm()

        venue_id = form.venue_id.data
        artist_id = form.artist_id.data
        start_time = form.start_time.data

        connection = psycopg2.connect(DatabaseURI.SQLALCHEMY_DATABASE_URI)
        cursor = connection.cursor()

        cursor.execute(f'''
      insert into show_items(artist_id, venue_id, start_time)
      values({artist_id}, {venue_id}, '{start_time}')
      ''')

        connection.commit()

        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except BaseException:
        # e.g., flash('An error occurred. Show could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        flash('An error occured Show was not successfully listed!')
        print(sys.exc_info())
    finally:
        connection.close()

    return render_template('pages/home.html')
