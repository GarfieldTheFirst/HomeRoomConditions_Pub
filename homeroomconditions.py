from app import create_app, db, data_collector_handler, \
    sensor_simulator_handler
from sqlalchemy_utils import database_exists
from app.models.roomdata import Device as DB_Device, Roomdata, Hour, User, \
    Role, Permission
from config import Config, Development
import os


selected_configuration = Config
if os.environ.get("FLASK_CONFIG") == "development":
    selected_configuration = Development

app = create_app(config_class=selected_configuration)

with app.app_context() as ac:
    if not database_exists(db.engine.url):
        db.create_all()
        Role.insert_roles()
        admin_user = User(username='admin', email=Config.APP_ADMIN)
        admin_user.set_password(Config.APP_ADMIN_CRED)
        admin_user.role = Role.query.filter_by(name='Administrator').first()
        db.session.add(admin_user)
        db.session.commit()


data_collector_handler.app = app
sensor_simulator_handler.update_simulated_devices()
data_collector_handler.update_devices_to_be_monitored()


@app.shell_context_processor
def make_shell_context():
    return {'db': db,
            'Roomdata': Roomdata,
            'Hour': Hour,
            'DB_Device': DB_Device,
            'User': User,
            'Role': Role,
            'Permission': Permission}


app.logger.info("Startup complete")

if __name__ == "__main__":  # not the case if served by waitress
    if selected_configuration in [Development]:
        app.run(use_debugger=False, use_reloader=False,
                passthrough_errors=True, port=8000)
