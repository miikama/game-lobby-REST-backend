from flask import Blueprint
from flask_cors import CORS

api_routes = Blueprint('api', __name__, template_folder='templates')


# add cors to the api routes
CORS(api_routes)


@api_routes.route("/")
@api_routes.route("/index")
def index():
    return "<h1>Hello World!</h1>"


# import the app routes
from krokeapp.apiroutes import player_routes
from krokeapp.apiroutes import game_routes
from krokeapp.apiroutes import team_routes