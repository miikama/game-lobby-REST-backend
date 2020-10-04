

import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from krokeapp.config import Config


__version__ = 0.1


# init database object (does not load or create the database)
db = SQLAlchemy()

logger = logging.getLogger("Krokeapp")
logger.setLevel(logging.INFO)


def create_app(config):
    """
        Encapsulate the app creation in a method 
        to allow creating the application with different 
        configurations
    """
    assert( isinstance(config, Config) )

    # init flask app
    app = Flask(__name__)

    # update the application config with our configuration
    app.config.from_object(config)

    # will be disabled in future
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # give the app to the database instance
    db.init_app(app)
    
    # load the application url endpoints
    from krokeapp.apiroutes import api_routes
    app.register_blueprint(api_routes)

    return app




