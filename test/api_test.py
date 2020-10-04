


import unittest
import sys
import os
import json

from flask import url_for

# add the parent directory to path for importing krokeapp
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from krokeapp import db, create_app
from krokeapp.config import Config
from krokeapp.database import fill_database, init_database
from krokeapp import logger
from krokeapp.utils import get_from_dict
from krokeapp.status_codes import *

TEST_DATABASE = "test.db"

# helper methods for api calls, these should be combined with the main app
def player_payload(name="", pid=""):
	return json.dumps({"player": {"name": name, "id": pid}})



class TestConfig(Config):
	
	SQLALCHEMY_DATABASE_URI = "sqlite:///" + TEST_DATABASE

class TestApi(unittest.TestCase):

	def create_player(self, name=""):
		"""
			helper method for common action
		"""
		data = player_payload(name=name)
		res = self.client().post('players',
			data=data, content_type='application/json')	
		player_id = get_from_dict(res.json, ['player', 'id'])

		return res, player_id

	def create_game(self, owner_id):
		"""
			helper method for common action
		"""
		
		data = player_payload(pid=owner_id)
		res = self.client().post('/games',
								data=data,
								content_type='application/json')		
		game_id = get_from_dict(res.json, ['game', 'id'])

		return res, game_id

	def create_team(self, game_id, owner_id):
		"""
			helper method for common action
		"""
		res = self.client().post('games/game'+str(game_id)+'/teams',
								data=player_payload(pid=owner_id),
								content_type='application/json')		
		team_id = get_from_dict(res.json, ['team', 'id'])

		return res, team_id

	def join_game(self, player_id, game_id):
		"""
			helper method for common action
		"""
		res = self.client().put('games/game'+str(game_id),
								data=player_payload(pid=player_id),
								content_type='application/json')		
		return res

	def join_team(self, game_id, team_id, player_id):
		"""
			helper method for common action
		"""
		# join team
		res = self.client().put('games/game' + str(game_id) + '/teams/team' + str(team_id),
								data=player_payload(pid=player_id),
								content_type='application/json')					
		return res


	@classmethod
	def setUpClass(cls):
		"""
			Create a test database and init app
			once for each tests
		"""

		# update the application config with our configuration
		config = TestConfig()

		# create the app with our test config
		cls.app = create_app(config)

		# use a test client to test the api
		cls.client = cls.app.test_client

		# the database needs an active application
		with cls.app.app_context():
			init_database(db, cls.app)		

	@classmethod
	def tearDownClass(cls):
		# after running the tests, delete the test database
		# will run to file path problems at some point
		try:
			os.remove('krokeapp/' + TEST_DATABASE)
		except FileNotFoundError:
			logger.warning("Cannot remove test database, did not find it.")
			

	def test_create_player(self):		
		pname = "test_name"
		res, player_id = self.create_player(pname)

		self.assertEqual(res.status_code, RESOURCE_CREATED)

		# created id should be part of payload		
		self.assertNotEqual(player_id, None)

		# given name should be the returned name
		new_name = get_from_dict(res.json, ['player', 'name'])
		self.assertEqual(new_name, pname)

		# the location of the new resource should be set
		self.assertNotEqual(res.location, None)


	def test_change_player_name(self):
		# create player
		pname = "test_name"					
		res, player_id = self.create_player(pname)

		# change the name of the created player
		new_name = "new_name"		
		data = player_payload(name=new_name, pid=player_id)		
		res = self.client().patch('/players/player' + str(player_id),
			data=data, content_type='application/json')				

		# code should be 200
		self.assertEqual(res.status_code, SUCCESS)

		# get all player resources from the server
		res = self.client().get('/players')

		for player in res.json.get('players'):
			# the name of the player with the id of the created player should match
			if get_from_dict(player, ['player', 'id']) == player_id:				
				self.assertEqual(new_name, get_from_dict(player, ['player', 'name']))


	def test_create_game(self):
		# create player to own the game
		res, player_id = self.create_player("owner")

		self.assertEqual(res.status_code, RESOURCE_CREATED)

		data = player_payload(pid=player_id)
		res = self.client().post('/games',
								data=data,
								content_type='application/json')

		# game creation should be succesful
		self.assertEqual(res.status_code, RESOURCE_CREATED)

		# the creator should be set as the owner
		owner_id = get_from_dict(res.json, ['game', 'owner', 'player', 'id'])
		self.assertEqual(owner_id, player_id)

		# the location of the new resource should be set		
		self.assertNotEqual(res.location, None)

	def test_join_game(self):
		# create player to own the game
		res, player_id = self.create_player("owner2")

		# create empty game for joining
		res, game_id = self.create_game(player_id)

		# game creation should be succesful
		self.assertEqual(res.status_code, RESOURCE_CREATED)

		# join the owner to the game
		res = self.join_game(player_id, game_id)
								
		# create another player and add them to the game
		res, an_id = self.create_player("another dude")
		res = self.join_game(an_id, game_id)

		# query the players in the game
		res = self.client().get("/games/game"+str(game_id))

		# the player structures in the response
		players = get_from_dict(res.json, ['game', 'players'])
		# get the player ids
		player_ids = [get_from_dict(player, ['player', 'id']) for player in players]

		# we've added two players -> game should have two participants
		self.assertTrue(len(player_ids) == 2)

		# make sure the ids are in the game players
		for pid in (player_id, an_id):
			self.assertIn(pid, player_ids)	

	def test_leave_game(self):
		
		# create player and add to game
		res, player_id = self.create_player('quitter')
		res, game_id = self.create_game(player_id)
		self.join_game(player_id, game_id)

		# leave game
		data = player_payload(pid=player_id)
		# change the payload
		del_data = data.replace('player', 'del_player', 1)
		res = self.client().patch('/games/game'+str(game_id),
									data=del_data,
									content_type='application/json')

		#confirm status code
		self.assertEqual(res.status_code, SUCCESS)
		
		# after leaving the game game should have no players left
		res = self.client().get('games/game'+str(game_id))
		players = get_from_dict(res.json, ['game', 'players'])

		self.assertEqual(len(players), 0)


	def test_leave_game_and_team(self):
		
		# create player and add to game
		res, player_id = self.create_player('quitter')
		res, game_id = self.create_game(player_id)
		self.join_game(player_id, game_id)
		res, team_id = self.create_team(game_id, player_id)
		self.join_team(game_id, team_id, player_id)

		# game should initially have one team
		res = self.client().get('games/game'+str(game_id)+'/teams')
		teams = get_from_dict(res.json, ['teams'])
		self.assertTrue(len(teams) == 1)

		# leave game
		data = player_payload(pid=player_id)
		# change the payload
		del_data = data.replace('player', 'del_player', 1)
		res = self.client().patch('/games/game'+str(game_id),
									data=del_data,
									content_type='application/json')

		#confirm status code
		self.assertEqual(res.status_code, SUCCESS)
		
		# after leaving the owned team, the team should be gone
		res = self.client().get('games/game'+str(game_id)+'/teams')
		teams = get_from_dict(res.json, ['teams'])
		self.assertTrue(len(teams) == 0)

	def test_delete_game(self):

		# create player and add to game
		res, player_id = self.create_player('quitter')
		res, game_id = self.create_game(player_id)
		self.join_game(player_id, game_id)
		res, team_id = self.create_team(game_id, player_id)
		self.join_team(game_id, team_id, player_id)

		# deleting the game as the owner
		res = self.client().delete('games/game'+str(game_id),
									data=player_payload(pid=player_id),
									content_type='application/json')

		# query for games and make sure the game is no more
		res = self.client().get('games')

		for game in get_from_dict(res.json, ['games']):
			gid = get_from_dict(game, ['game', 'id'])
			self.assertNotEqual(gid, game_id)		


	def test_create_team(self):

		# create a player 
		res, player_id = self.create_player('team_player')
		self.assertEqual(res.status_code, RESOURCE_CREATED)
		# create game
		res, game_id = self.create_game(player_id)
		self.assertEqual(res.status_code, RESOURCE_CREATED)

		# try to create team in a game without joining
		res, team_id = self.create_team(game_id, player_id)

		# check for the expected status code
		self.assertEqual(res.status_code, PRECONDITION_FAILED)

		# join the game
		res = self.join_game(player_id, game_id)

		# then try to create a team				
		res, team_id = self.create_team(game_id, player_id)
		
		# it should be succesful
		self.assertTrue(res.status_code, RESOURCE_CREATED)

		# check that the team is listed under the game with the team
		res = self.client().get('games/game'+str(game_id)+'/teams')

		teams = get_from_dict(res.json, ['teams'])

		# should only be one team created
		self.assertTrue(len(teams) == 1)
		
		self.assertEqual(get_from_dict(teams[0], ['team', 'id']), team_id)


	def test_join_team(self):
		# create player
		res, player_id = self.create_player('joining_player')
		# create game
		res, game_id = self.create_game(player_id)
		# join the player to the game
		self.join_game(player_id, game_id)
		# create team in the game
		res, team_id = self.create_team(game_id, player_id)

		# join team
		res = self.client().put('games/game' + str(game_id) + '/teams/team' + str(team_id),
								data=player_payload(pid=player_id),
								content_type='application/json')

		# check the status code
		self.assertEqual(res.status_code, SUCCESS)

		# get the team and check that the player actually is there
		res = self.client().get('games/game' + str(game_id) + '/teams/team' + str(team_id))

		players = get_from_dict(res.json, ['team', 'players'])

		# should have one player
		self.assertEqual(len(players), 1)

		# the player id should be the one added
		self.assertEqual(get_from_dict(players[0], ['player', 'id']), player_id)

	def test_leave_team(self):

		# create player and add to game
		res, player_id = self.create_player('quitter')
		res, game_id = self.create_game(player_id)
		self.join_game(player_id, game_id)
		res, team_id = self.create_team(game_id, player_id)
		self.join_team(game_id, team_id, player_id)

		# create another dude
		res, side_id = self.create_player('sidekick')
		self.join_game(side_id, game_id)
		self.join_team(game_id, team_id, side_id)

		# team should have these two players
		res = self.client().get('games/game'+str(game_id) + '/teams')

		# get the players of the only team in this game
		teams = get_from_dict(res.json, ['teams'])
		players = get_from_dict(teams[0], ['team', 'players'])
		for player in players:
			self.assertIn(get_from_dict(player, ['player', 'id']), (player_id, side_id))

		# modify payload for deleting player
		data = player_payload(pid=side_id).replace('player', 'del_player', 1)
		res = self.client().patch('games/game'+str(game_id) + '/teams/team' + str(team_id),
								  data=data, content_type='application/json')

		# check status code
		self.assertEqual(res.status_code, SUCCESS)

		# the team should now only have one player, which is the original player
		res = self.client().get('games/game'+str(game_id) + '/teams')
		teams = get_from_dict(res.json, ['teams'])
		players = get_from_dict(teams[0], ['team', 'players'])
		for player in players:
			self.assertEqual(get_from_dict(player, ['player', 'id']), player_id)

		# leave with the owner of the team as well
		# modify payload for deleting player
		data = player_payload(pid=player_id).replace('player', 'del_player', 1)
		res = self.client().patch('games/game'+str(game_id) + '/teams/team' + str(team_id),
								  data=data, content_type='application/json')

		self.assertEqual(res.status_code, SUCCESS)

		# check that the team is destroyed when the owner leaves
		res = self.client().get('games/game'+str(game_id) + '/teams')
		teams = res.json['teams']
		
		self.assertTrue(len(teams) == 0)

	
	def test_delete_team(self):
		pass



if __name__ == '__main__':
	unittest.main()