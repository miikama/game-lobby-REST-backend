


from flask import Blueprint
from flask import jsonify, request, url_for, Response
from krokeapp import db
from krokeapp import logger
from krokeapp.models import Player, Game, Team
from krokeapp.status_codes import *

api_routes = Blueprint('api', __name__, template_folder='templates')

def get_from_dict(d, key_list):
    """ 
        Go deeper into the dictionary layer by layer 
        and return the value of the key or None
    """
    if not d:
        return None

    d_inner = d
    for key in key_list:
        d_inner = d_inner.get(key)
        if d_inner is None:
            return None

    return d_inner

@api_routes.route("/")
@api_routes.route("/index")
def index():
    return "<h1>Hello World!</h1>"


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


@api_routes.route("/games/game<gameid>/teams", methods=['GET', 'POST'])
def teams(gameid):

    rjson = request.get_json()

    # create a team
    if request.method == 'POST':
        # the player creating the team
        pid = get_from_dict(rjson, ['player', 'id'])
        player = Player.by_id(pid)
        # the game the team is added to
        game = Game.by_id(gameid)
        # the new name of the team (if given)
        team_name = get_from_dict(rjson, ['team', 'name'])

        # trying to create with nonexisting player or team
        if player is None or game is None:
            return jsonify(''), UNPROCESSABLE

        # player has to be in the game the team is being created
        if player.game is not game:
            return jsonify(''), PRECONDITION_FAILED

        # create team                
        team = Team.new_team(game, player, name=team_name)
        return jsonify(team.to_json())    


    # get the teams
    if request.method == 'GET':             
        return jsonify(Team.teams_to_json(gameid=gameid))

@api_routes.route("/games/game<gameid>/teams/team<teamid>", methods=['PUT', 'PATCH', 'GET', 'DELETE'])
def team(gameid, teamid):

    rjson = request.get_json()

    # players can join the team
    if request.method == 'PUT':
        # get the player wanting to join
        pid = get_from_dict(rjson, ['player', 'id'])
        player = Player.by_id(pid)

        # get the target game
        game = Game.by_id(gameid)

        # get the target team
        team = Team.by_id(teamid)

        # cannot join nonexisting game
        if player is None or game is None or team is None:
            return jsonify(), PRECONDITION_FAILED

        # cannot add player twice
        if player in team.players:
            return jsonify(), PRECONDITION_FAILED

        # add player only to team in the game they are in
        if player.game is not team.game:
            return jsonify(), PRECONDITION_FAILED
        
        team.add_player(player)
        return jsonify(), SUCCESS

        
    # If the request body containes 'del_player'
    # it is used to remove the player from the team
    if request.method == 'PATCH':

        game = Game.by_id(gameid)
        team = Team.by_id(teamid)

        # trying to modify non-existing game
        if game is None or team is None:
            return jsonify(), UNPROCESSABLE

        # remove player from team
        pid = get_from_dict(rjson, ['del_player', 'id'])        
        player = Player.by_id(pid)
        if player is not None:

            # cannot leave from game or team player is not in
            if player.game is not game or player.team is not team:
                return jsonify(), PRECONDITION_FAILED

            # if owner of the team, team disbands
            if player is player.team.owner:
                Team.remove_team(player.team)

            # leave the team (if in one)            
            player.leave_team()            

            return jsonify(), SUCCESS

        return jsonify(), UNPROCESSABLE

    # return team info
    if request.method == 'GET':
        team = Team.by_id(teamid)
        if team is not None:
            return jsonify(team.to_json())
        else:
            return jsonify(), UNPROCESSABLE

    # owner can remove team
    if request.method == 'DELETE':

        # player wanting to delete the game
        player_id = get_from_dict(rjson, ['player', 'id'])
        player = Player.by_id(player_id)
        
        # game to be deleted
        team = Team.by_id(teamid)
        if player is None or team is None:
            return jsonify(), UNPROCESSABLE

        # only the owner can delete the game
        if team.owner is not player:
            return jsonify(), UNAUTHORIZED

        # finally delete the game
        Team.remove_team(team)

        return jsonify(), SUCCESS


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

    # after disconnecting
    if request.method == 'DELETE':
        pass

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












