import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from config import Config

bootstrap = Bootstrap()
db = SQLAlchemy()
migrate = Migrate()
moment = Moment()


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
    bootstrap.init_app(app)
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    moment.init_app(app)

    from app.views import views
    from app.devices import bpr as devices_bp
    from app.settings import bpr as settings_bp

    app.register_blueprint(views)
    app.register_blueprint(devices_bp, url_prefix='/devices')
    app.register_blueprint(settings_bp, url_prefix='/settings')

    return app


from app import models
from app.data_collector.data_collector_handler import DataCollectorHandler
from app.sensorsimulator.simulator_handler import SensorSimulatorHandler

data_collector_handler = DataCollectorHandler(app=None, db=db)
sensor_simulator_handler = SensorSimulatorHandler()
