


class Game:

	team_counter = 1

	def __init__(self, game_id):
		self.gameID = game_id

		# player_id -> player
		self.players = dict()

		# team_id -> [player_id, ...]
		self.teams = dict()

		# keep track which team the player is in
		self.player_teams = dict()


	def add_player(self, player)
		self.players[player.playerID] = player

	def remove_player(self, player):
		if player.playerID in self.players:
			del self.players[player.playerID]

	def get_teams(self):
		return self.teams



	def add_player_to_team(self,  player_id, team_id):

		# player already in team
		if player_id in self.player_teams:
			self.update_player_team(player_id, team_id)
		else:
			# team exists
			if team_id in self.teams:
				self.teams[team_id] = player_id
				self.player_teams[player_id] =  

	def update_player_team(self, player_id, team_id):
		# remove player from current team
		del self.teams[self.player_teams[self.player_id]]
		# put player to new team



	def remove_player_from_team(self, player, team_id):





	def __repr(self):
		return f"Game with {len(self.teams)} teams and {len(self.players)} players."
		
