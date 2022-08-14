import numpy as np

from athletes import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150))
    password = db.Column(db.String(150))
    admin = db.Column(db.Boolean)


class Athlete(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    year_of_birth = db.Column(db.Integer)
    gender = db.Column(db.String(150))
    ladv_athlete_number = db.Column(db.Integer)
    ladv_id = db.Column(db.Integer)

    def get_personal_best(self, discipline):
        performances = Performance.query.filter_by(athlete_id=self.id, discipline=discipline)
        return np.max([float(p.value.replace(",", ".")) for p in performances])


class Performance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(150))
    city = db.Column(db.String(150))
    athlete_id = db.Column(db.Integer, db.ForeignKey('athlete.id'))
    discipline = db.Column(db.String(150))
    value = db.Column(db.String(150))
    unit = db.Column(db.String(150))
    wind = db.Column(db.Float)
    placement = db.Column(db.Integer)
    championship = db.Column(db.String(150))
    indoor = db.Column(db.Boolean)
