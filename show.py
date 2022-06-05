from flask import (
    Blueprint,
    render_template,
    flash,
    redirect,
    url_for
)
from model import Artist, db, Show, Venue
import sys
from forms import *
from model import Artist, Venue

show_blueprint = Blueprint('show_blueprint', __name__)


#  Shows
#  ----------------------------------------------------------------

@show_blueprint.route('/shows')
def shows():
    # displays list of shows at /shows
    try:
        data = []

        stmt = db.session.query(Show, Venue, Artist).select_from(
            Show).join(Venue).join(Artist).all()

        for show, venue, artist in stmt:
            data.append({
                "venue_id": venue.id,
                "venue_name": venue.name,
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": show.start_time
            })

    except BaseException:
        flash(f'An error occured, could not get all shows successfully!')
        print(sys.exc_info())

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

        show = Show(
            venue_id=venue_id,
            artist_id=artist_id,
            start_time=start_time)

        db.session.add(show)
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except BaseException:
        # e.g., flash('An error occurred. Show could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        db.session.rollback()
        flash('An error occured Show was not successfully listed!')
        print(sys.exc_info())
    finally:
        db.session.close()

    return redirect(
        url_for('index'))
