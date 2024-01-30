import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from config import Config


convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

bootstrap = Bootstrap()
metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(session_options={"expire_on_commit": False}, metadata=metadata)
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
migrate = Migrate()
moment = Moment()
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    if not app.debug:
        # Setup logfile
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/homeroomconditions.log',
                                           maxBytes=10240,
                                           backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: \
                %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Homeroomconditions startup')
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    bootstrap.init_app(app)
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    moment.init_app(app)
    mail.init_app(app)

    from app.home import bpr as home_bp
    from app.devices import bpr as devices_bp
    from app.settings import bpr as settings_bp
    from app.auth import bpr as auth_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(devices_bp, url_prefix='/devices')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app


from app import models
from app.data_collector.data_collector_handler import DataCollectorHandler
from app.sensorsimulator.simulator_handler import SensorSimulatorHandler

data_collector_handler = DataCollectorHandler(app=None, db=db)
sensor_simulator_handler = SensorSimulatorHandler()
