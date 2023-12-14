from flask import Blueprint

bpr = Blueprint('auth', __name__)

from app.auth import routes
