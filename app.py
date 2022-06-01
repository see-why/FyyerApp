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
    flash(f'An error occured could not search with {partial_name} was not successfully!')
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
  return render_template('pages/home.html')
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
    flash(f'An error occured could not search with {partial_name} was not successfully!')
    print(sys.exc_info())
  finally:
    connection.close()

  return render_template('pages/search_artists.html', results=response, search_term=partial_name)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  data1={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "past_shows": [{
      "venue_id": 1,
      "venue_name": "The Musical Hop",
      "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
      "start_time": "2019-05-21T21:30:00.000Z"
    }],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0,
  }
  data2={
    "id": 5,
    "name": "Matt Quevedo",
    "genres": ["Jazz"],
    "city": "New York",
    "state": "NY",
    "phone": "300-400-5000",
    "facebook_link": "https://www.facebook.com/mattquevedo923251523",
    "seeking_venue": False,
    "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "past_shows": [{
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2019-06-15T23:00:00.000Z"
    }],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0,
  }
  data3={
    "id": 6,
    "name": "The Wild Sax Band",
    "genres": ["Jazz", "Classical"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "432-325-5432",
    "seeking_venue": False,
    "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "past_shows": [],
    "upcoming_shows": [{
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-01T20:00:00.000Z"
    }, {
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-08T20:00:00.000Z"
    }, {
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-15T20:00:00.000Z"
    }],
    "past_shows_count": 0,
    "upcoming_shows_count": 3,
  }
  data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
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


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []
  

  data=[{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21T21:30:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15T23:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-01T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-08T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-15T20:00:00.000Z"
  }]
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
