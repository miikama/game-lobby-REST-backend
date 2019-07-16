from krokeapp import create_app
from krokeapp.config import Config

# Create an entry point for wsgi server used in production.
#
# e.g.the application can be run with gunicorn with
# 
#  $gunicorn krokeapp.runner:app

class DeploymentConfiguration(Config):
    pass


app = create_app(DeploymentConfiguration())


