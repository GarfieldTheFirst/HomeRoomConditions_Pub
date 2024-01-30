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
    USER_DB_NAME = os.environ.get('USER_DB_NAME')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///data/{DB_NAME}'
    SQLALCHEMY_BINDS = {
        'db2': f'sqlite:///data/{USER_DB_NAME}'
    }
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    LANGUAGES = ['en', 'de']
    ADMINS = [os.environ.get('MAIL_USERNAME')]
    ADMINS.append(os.environ.get('ADMINS'))
    APP_ADMIN = os.environ.get('APP_ADMIN')
    APP_ADMIN_CRED = os.environ.get('APP_ADMIN_CRED')


class Development(Config):
    pass # nothing here right now...


class TestConfig(Config):
    DB_NAME = "database_test.db"
    SQLALCHEMY_DATABASE_URI = f'sqlite:///data/{DB_NAME}'
