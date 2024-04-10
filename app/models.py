from . import db
from flask_login import UserMixin
from datetime import datetime
from random import randint

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    plan = db.Column(db.String(20), nullable=False, default='Grátis')
    user_pic = db.Column(db.String(250), nullable=False, default=f"/static/images/user_pictures/user{randint(1, 6)}.webp")
    two_factor_secret = db.Column(db.String(100))
    reports = db.relationship('Report', backref='author', lazy=True)

class Report(db.Model):
    report_id = db.Column(db.String(100), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    title = db.Column(db.String(100), nullable=False)

class Trash(db.Model):
    report_id = db.Column(db.String(100), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    title = db.Column(db.String(100), nullable=False)
