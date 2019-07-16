from krokeapp import db, create_app
from krokeapp.config import Config
from krokeapp.database import init_if_not_found
# Create an entry point for wsgi server used in production.
#
# e.g.the application can be run with gunicorn with
# 
#  $gunicorn krokeapp.runner:app

class DeploymentConfiguration(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///production.db"


app = create_app(DeploymentConfiguration())

# initialize db if not already done
init_if_not_found(db, app)
