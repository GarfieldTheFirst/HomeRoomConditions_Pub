from flask import Blueprint

bpr = Blueprint('devices',
                __name__,
                template_folder='templates/devices')

from app.devices import routes
