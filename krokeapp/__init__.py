

import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from krokeapp.config import Config


__version__ = 0.1


# init flask app
app = Flask(__name__)


# update the application config with our configuration
Config().update_app_config(app)


# init database
db = SQLAlchemy(app)

logger = logging.getLogger("Krokeapp")
logger.setLevel(logging.INFO)


from krokeapp import routes
