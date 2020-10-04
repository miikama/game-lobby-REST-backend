
from flask import jsonify, request, url_for, Response
from krokeapp import db
from krokeapp import logger
from krokeapp.models import Player, Game, Team
from krokeapp.status_codes import *
from krokeapp.utils import get_from_dict

from krokeapp.apiroutes import api_routes

@api_routes.route("/games", methods=['GET', 'POST'])
def games():
    """end-point for creating games and getting game info."""

    if request.method == 'GET':				
        return jsonify(Game.games_to_json()) 

    if request.method == 'POST':
        pjson = request.get_json()
        # player id 
        player_id = get_from_dict(pjson, ['player', 'id'])
        if player_id is not None:	
            db_player = Player.query.filter_by(id=player_id).first()
            if db_player is not None:
                game = Game.new_game(db_player)
                response = jsonify(game.to_json())
                response.status_code = RESOURCE_CREATED
                response.headers['location'] = 'games/game' + str(game.id)
                return response

    return jsonify(''), UNPROCESSABLE


@api_routes.route("/games/game<id>", methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def game(id):
    """End-point for accessing a specific game."""

    # get the json body
    rjson = request.get_json()
	
    # patch is used for a quite a lot
    # 1. if the request body contains 'game',
    # it can be used to update the game properties.
    # 2. if the request body containes 'del_player'
    # it is used to remove the player from the game
    if request.method == 'PATCH':

        game = Game.by_id(id)

        # trying to modify non-existing game
        if game is None:
            return jsonify(), UNPROCESSABLE

        # remove player from game and team
        pid = get_from_dict(rjson, ['del_player', 'id'])        
        player = Player.by_id(pid)
        if player is not None:

            # cannot leave from game player is not in
            if player.game is not game:
                return jsonify(), PRECONDITION_FAILED

            # The teams are under the game, leave the team 
            # if owner of the team, team disbands
            if player.team is not None:                
                if player is player.team.owner:
                    Team.remove_team(player.team)

            # leave the team (if in one)            
            player.leave_team()            

            # leave game
            player.leave_game()

            return jsonify(), SUCCESS

        else:
            return jsonify(), UNPROCESSABLE

      
    # send out info for this game specifically
    if request.method == 'GET':
        # find the game
        game = Game.by_id(id)
        # only send out info of existing games
        if game is not None:
            return jsonify(game.to_json())
        else:
            return jsonify(), UNPROCESSABLE

    # people can join the game
    if request.method == 'PUT':
        # find the game
        game = Game.by_id(id)
        # id of the player wanting to join
        pid = get_from_dict(rjson, ['player', 'id'])        
        player = Player.by_id(pid)
        # only add existing player to existing game
        if game is None or player is None:
            return jsonify(), UNPROCESSABLE

        # cannot add player twice
        if player in game.players:
            return jsonify(), UNPROCESSABLE

        game.add_player(player)
        return jsonify(), SUCCESS
        
    # owner can delete the game
    if request.method == 'DELETE':
        
        # player wanting to delete the game
        player_id = get_from_dict(rjson, ['player', 'id'])
        player = Player.by_id(player_id)
        # game to be deleted
        game = Game.by_id(id)
        if player is None or game is None:
            return jsonify(), UNPROCESSABLE
        # only the owner can delete the game
        if game.owner is not player:
            return jsonify(), UNAUTHORIZED

        # finally delete the game
        Game.remove_game(game)

        return jsonify(), SUCCESS
