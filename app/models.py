# models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(80), primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    pic = db.Column(db.String(255))
    password = db.Column(db.String(200), nullable=False)

class Report(db.Model):
    __tablename__ = 'reports'
    report_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(80), db.ForeignKey('users.username'), nullable=False)
    user = db.relationship('User', backref=db.backref('reports', lazy=True))
