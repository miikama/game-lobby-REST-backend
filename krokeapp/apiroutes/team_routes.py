from flask import jsonify, request, url_for, Response
from krokeapp import db
from krokeapp import logger
from krokeapp.models import Player, Game, Team
from krokeapp.status_codes import *
from krokeapp.utils import get_from_dict

from krokeapp.apiroutes import api_routes

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












