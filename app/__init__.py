import os
import secrets
from flask import Flask
from datetime import timedelta

def create_app():
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(16)
    app.permanent_session_lifetime = timedelta(days=1)
    app.config['IMAGE_UPLOADS'] = os.path.join(os.getcwd(), 'app', 'static', 'uploads')

    from app.routes import init_routes
    init_routes(app)

    return app