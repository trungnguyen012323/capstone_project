from flask_sqlalchemy import SQLAlchemy
from config import database_setup

db = SQLAlchemy()

def setup_db(app):
    database_setup(app)  # Thiết lập cấu hình cơ sở dữ liệu
    db.app = app
    db.init_app(app)

def db_drop_and_create_all():
    db.drop_all()
    db.create_all()

class Actor(db.Model):
    __tablename__ = 'actors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String, nullable=False)

    def format(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender
        }

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class Movie(db.Model):
    __tablename__ = 'movies'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    release_date = db.Column(db.Date, nullable=False)

    def format(self):
        return {
            'id': self.id,
            'title': self.title,
            'release_date': self.release_date
        }

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class Performance(db.Model):
    __tablename__ = 'performances'

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('actors.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    actor = db.relationship('Actor', backref=db.backref('performances', cascade='all, delete'))
    movie = db.relationship('Movie', backref=db.backref('performances', cascade='all, delete'))

    def format(self):
        return {
            'id': self.id,
            'actor_id': self.actor_id,
            'movie_id': self.movie_id,
            'actor': self.actor.format(),
            'movie': self.movie.format()
        }

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
