import os
from dotenv import load_dotenv
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    raise Exception


class Config(object):
    DATA_COLLECTION_INTERVAL_SECONDS = 60
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_NAME = os.environ.get('DB_NAME')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///data/{DB_NAME}'
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    LANGUAGES = ['en', 'de']
    ADMINS = []
    ADMINS.append(os.environ.get('ADMINS'))
    SIMULATED = True


class Development(Config):
    SIMULATED = True


class TestConfig(Config):
    SIMULATED = True
    DB_NAME = "database_test.db"
    SQLALCHEMY_DATABASE_URI = f'sqlite:///data/{DB_NAME}'
