from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

show_items = db.Table('show_items',
    db.Column('venue_id', db.Integer, db.ForeignKey('Venues.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('Artists.id'), primary_key=True),
    db.Column('start_time',db.String())
)

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
    artists = db.relationship('Artist', secondary=show_items, backref=db.backref('Venues',lazy=True))

    def __repr__(self):
        return f'Venue id: {self.id} name: {self.name} city: {self.city} state: {self.state}'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

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

    def __repr__(self):
        return f'Artist id: {self.id} name: {self.name} city: {self.city} state: {self.state}'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate