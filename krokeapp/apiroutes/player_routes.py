

from flask import jsonify, request, url_for, Response
from krokeapp import db
from krokeapp import logger
from krokeapp.models import Player, Game, Team
from krokeapp.status_codes import *
from krokeapp.utils import get_from_dict


from krokeapp.apiroutes import api_routes


@api_routes.route("/players", methods=['GET', 'POST'])
def players():

    # just for debugging get all the players
    if request.method == 'GET':
        return jsonify(Player.players_to_json()) 
	
    if request.method == 'POST':
        pjson = request.get_json()
        name = get_from_dict(pjson, ['player', 'name'])
        name = name if name is not None else "anonymous"        

        player = Player(name=name)

        response = jsonify(player.to_json())
        response.status_code = RESOURCE_CREATED
        response.headers['location'] = 'players/player'+ str(player.id)

        return response 



@api_routes.route("/players/player<playerid>", methods=['PATCH'])
def player(playerid):

    rjson = request.get_json()

    # player can update their name
    if request.method == 'PATCH':
        new_name = get_from_dict(rjson, ['player', 'name'])

        # update requires player hash corresponding 
        # to the playerid and the new name
        if new_name is not None:
            player = Player.query.filter_by(id=playerid).first()
            player.update_name(new_name)
            return jsonify(player.to_json()), SUCCESS			
        else:
            return jsonify('No name given.'), UNPROCESSABLE

