#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
from tracemalloc import start
from wsgiref.handlers import format_date_time
import dateutil.parser
import babel
from flask import Flask, jsonify, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from model import db, show_items, Venue, Artist
import psycopg2
from datetime import date
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db.init_app(app)

# TODO: connect to a local postgresql database

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  print('date',date)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  try:
    connection = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
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
      results[location].append({"id": id, "name": name, "num_upcoming_shows": show_count})    
    for key, value in results.items():
      data.append(
        {"city" : key[0],
          "state" : key[1],
          "venues": [{ "id": show['id'], "name": show['name'] , "num_upcoming_shows": show['num_upcoming_shows']} for show in value]
    })
  except:
    flash('An error occured venues was not successfully listed!')
    print(sys.exc_info())
  finally:
    connection.close()

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  try:
    partial_name = request.form.get('search_term', '')
    response = {}
    venues = Venue.query.filter(Venue.name.ilike(f'%{partial_name}%')).all()
    count = len(venues)

    if count > 0:

      if count > 1:
        list_of_ids = ",".join([str(item.id) for item in venues])
      elif count == 1:
        list_of_ids = str(venues[0].id)

      connection = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
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

  except:
    flash(f'An error occured, could not search with {partial_name} was not successfully!')
    print(sys.exc_info())
  finally:
    connection.close()
 
  return render_template('pages/search_venues.html', results=response, search_term=partial_name)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  try:
    connection = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
    cursor = connection.cursor()
    data = {}
    venue = Venue.query.get(venue_id)

    data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(','),
    "address": venue.address,
    "city": venue.city,
    "state":  venue.state,
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
    data['past_shows'] = [{ "artist_id": id,
      "artist_name":  name,
      "artist_image_link":  image_link,
      "start_time": start_time} for id, name, image_link, start_time in past_shows]
    data['past_shows_count'] = len(data['past_shows'])    

    cursor.execute(f''' 
      select a.id, a.name, a.image_link, s.start_time
      from "Artists" a join show_items s on a.id = s.artist_id where s.venue_id = {venue_id} and s.start_time >= '{date.today()}'     
      ''')

    upcoming_shows = cursor.fetchall()
    print('upcoming_shows',upcoming_shows)
    data['upcoming_shows'] = [{ "artist_id": id,
      "artist_name":  name,
      "artist_image_link":  image_link,
      "start_time": start_time} for id, name, image_link, start_time in upcoming_shows]
    data['upcoming_shows_count'] = len(data['upcoming_shows'])
    print('data',data)
  except:
    flash(f'Details for venue: {venue_id} was not successfully fetched!')
    print(sys.exc_info())
  finally:
    connection.close()

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  try:
    form = VenueForm()

    existing_venue = Venue.query.filter(Venue.name.ilike(f'%{form.name.data}%')).all()
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
  except:    
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    db.session.rollback()
    flash('An error occured Venue ' + request.form['name'] + ' was not successfully created!')
    print(sys.exc_info())
  finally:
    db.session.close()
    # TODO: modify data to be the data object returned from db insertion
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:   
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash(f'Venue: {venue_id} was successfully deleted!')
  except:
    flash(f'Venue: {venue_id} was not successfully deleted!')
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()
  return jsonify({'Success': True})
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  try:
    data = []
    artists = Artist.query.all()

    data = [ {
      "id": item.id,
      "name": item.name,
    } for item in artists]

    if len(data) > 0:
      flash('Artists successfully listed!') 
  except:
    flash('Artists was successfully listed!')
    print(sys.exc_info())

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  try:
    partial_name = request.form.get('search_term', '')
    response = {}
    artists = Artist.query.filter(Artist.name.ilike(f'%{partial_name}%')).all()
    count = len(artists)

    if count > 0:

      if count > 1:
        list_of_ids = ",".join([str(item.id) for item in artists])        
      elif count == 1:
        list_of_ids = str(artists[0].id)
      

      connection = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
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

  except:
    flash(f'An error occured, could not search with {partial_name} was not successfully!')
    print(sys.exc_info())
  finally:
    connection.close()

  return render_template('pages/search_artists.html', results=response, search_term=partial_name)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  try:
    connection = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
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
    data['past_shows'] = [{ "venue_id": id,
      "venue_name":  name,
      "venue_image_link":  image_link,
      "start_time": start_time} for id, name, image_link, start_time in past_shows]
    data['past_shows_count'] = len(data['past_shows'])    

    cursor.execute(f''' 
      select v.id, v.name, v.image_link, s.start_time
      from "Venues" v join show_items s on v.id = s.venue_id where s.artist_id = {artist_id} and s.start_time >= '{date.today()}' 
      ''')

    upcoming_shows = cursor.fetchall()
    print('upcoming_shows',upcoming_shows)
    data['upcoming_shows'] = [{ "venue_id": id,
      "venue_name":  name,
      "venue_image_link":  image_link,
      "start_time": start_time} for id, name, image_link, start_time in upcoming_shows]
    data['upcoming_shows_count'] = len(data['upcoming_shows'])
    print('data',data)
  except:
    flash(f'Details for venue: {artist_id} was not successfully fetched!')
    print(sys.exc_info())
  finally:
    connection.close()

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
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
  
  except:
    flash(f'Artist: {artist_id} was not successfully loaded!')
    print(sys.exc_info())

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  form = ArtistForm()
  try:
    artist = Artist.query.get(artist_id)

    existing_artist = Artist.query.filter(Artist.name.ilike(f'%{form.name.data}%')).all()
    if len(existing_artist) > 0 and form.name.data.lower() != artist.name.lower():
        print(form.name.data.lower(), artist.name.lower())
        flash('Artist ' + request.form['name'] + ' already exists!')
        return render_template('forms/edit_artist.html', form=form, artist=artist)

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
  except:
     flash(f'Artist: {artist_id} was not successfully edited!')
     print(sys.exc_info())
     db.session.rollback()
  finally:
    db.session.close()

  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  try:
      venue = Venue.query.get(venue_id)

      form.name.id = venue.name
      form.genres.data = venue.genres.split(',')
      form.address.data = venue.address
      form.city.data = venue.city
      form.state.data =  venue.state
      form.phone.data = venue.phone
      form.website_link.data = venue.website_link
      form.facebook_link.data = venue.facebook_link
      form.seeking_talent.data = venue.is_talent_seeking
      form.seeking_description.data = venue.talent_seeking_description
      form.image_link.data = venue.image_link
  except:
    flash(f'Venue: {venue_id} was not successfully loaded!')
    print(sys.exc_info())
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  try:
      venue = Venue.query.get(venue_id)
      form = VenueForm()

      existing_venue = Venue.query.filter(Venue.name.ilike(f'%{form.name.data}%')).all()
      if len(existing_venue) > 0 and form.name.data.lower() != venue.name.lower():
        print(form.name.data.lower(), venue.name.lower())
        flash('Venue ' + request.form['name'] + ' already exists!')
        return render_template('forms/edit_venue.html', form=form, venue=venue)

      genres = ",".join(form.genres.data)

      venue.name=form.name.data
      venue.city=form.city.data
      venue.state=form.state.data
      venue.address=form.address.data
      venue.phone=form.phone.data
      venue.genres=genres
      venue.image_link=form.image_link.data
      venue.facebook_link=form.facebook_link.data
      venue.website_link=form.website_link.data
      venue.is_talent_seeking=form.seeking_talent.data
      venue.talent_seeking_description=form.seeking_description.data

      db.session.commit()
      flash(f'Venue: {venue_id} was successfully edited!')
  except:
     flash(f'Venue: {venue_id} was not successfully edited!')
     print(sys.exc_info())
     db.session.rollback()
  finally:
    db.session.close()
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  try:
    form = ArtistForm()

    existing_artist = Artist.query.filter(Artist.name.ilike(f'%{form.name.data}%')).all()
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
  except:    
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    db.session.rollback()
    flash('An error occured Artist ' + request.form['name'] + ' was not successfully listed!')
    print(sys.exc_info())
  finally:
    db.session.close()
 
  return render_template('pages/home.html')

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:   
    artist = Artist.query.get(artist_id)
    db.session.delete(artist)
    db.session.commit()
    flash(f'Artist: {artist_id} was successfully deleted!')
  except:
    flash(f'Artist: {artist_id} was not successfully deleted!')
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()
  return jsonify({'Success': True})
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  try:
    data = []

    connection = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
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
  except:
    flash(f'An error occured, could not get all shows successfully!')
    print(sys.exc_info())
  finally:
    connection.close()
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
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

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
   try:
      form = ShowForm()

      venue_id=form.venue_id.data
      artist_id=form.artist_id.data
      start_time = form.start_time.data

      connection = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
      cursor = connection.cursor()

      cursor.execute(f''' 
      insert into show_items(artist_id, venue_id, start_time)
      values({artist_id}, {venue_id}, '{start_time}')
      ''')

      connection.commit()     

      # on successful db insert, flash success
      flash('Show was successfully listed!')
   except:    
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      flash('An error occured Show was not successfully listed!')
      print(sys.exc_info())
   finally:
       connection.close()

   return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
