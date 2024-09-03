import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    XML_OUTPUTS = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'xmls')