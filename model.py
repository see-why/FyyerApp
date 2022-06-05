from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Show(db.Model):
  __tablename__ = 'show_items'
  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey(
      'Artists.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venues.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)

  def __repr__(self):
      return f'Show artist_id: {self.artist_id} venue_id: {self.venue_id}'



class Venue(db.Model):
    __tablename__ = 'Venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String())
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    is_talent_seeking = db.Column(db.Boolean, nullable=False, default=False)
    talent_seeking_description = db.Column(db.String())
    shows = db.relationship('Show', backref='Artist', lazy=True)

    def __repr__(self):
        return f'Venue id: {self.id} name: {self.name} city: {self.city} state: {self.state}'


class Artist(db.Model):
    __tablename__ = 'Artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String())
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    is_venue_seeking = db.Column(db.Boolean, nullable=False, default=False)
    venue_seeking_description = db.Column(db.String())
    shows = db.relationship('Show', backref='Venue', lazy=True)

    def __repr__(self):
        return f'Artist id: {self.id} name: {self.name} city: {self.city} state: {self.state}'
