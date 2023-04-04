from flask import Blueprint

bpr = Blueprint('settings',
                __name__,
                template_folder='templates/devices')

from app.settings import routes
