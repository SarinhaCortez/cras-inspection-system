import os
import secrets
from flask import Flask
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from app.models import db

def create_app():
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(16)
    app.permanent_session_lifetime = timedelta(days=1)

    app.config['IMAGE_UPLOADS'] = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
    app.config['XML_OUTPUTS'] = os.path.join(os.getcwd(), 'app', 'static', 'xmls')

    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    from app.routes import init_routes
    init_routes(app)

    db.init_app(app)

    return app 
