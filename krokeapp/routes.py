

from flask import jsonify, request, url_for, Response
from krokeapp import app, db
from datetime import datetime

from krokeapp import logger


# HTTP response codes

UNPROCESSABLE = 422
UNAUTHORIZED = 401


def get_from_dict(d, key_list):
	""" 
		Go deeper into the dictionary layer by layer 
		and return the value of the key or None
	"""
	d_inner = d
	for key in key_list:
		d_inner = d_inner.get(key)
		if d_inner is None:
			return None

	return d_inner



# create a table for mapping multiple games to multiple players
# game_player_table = db.Table('association', db.Base.metadata,
#     db.Column('left_id', Integer, db.ForeignKey('left.id')),
#     db.Column('right_id', Integer, db.ForeignKey('right.id'))
# )


class Game(db.Model):
    # __tablename__ = 'right'

    counter = 0

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    name = db.Column(db.String(30), unique=False, nullable=False)

    # set up owner relationships
    #owner_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    #owner = db.relationship("Player", back_populates="owned_games", foreign_keys=['Player.owned_id'], uselist=False)
    
    # set up players in the game    
    #players_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    #players = db.relationship('Player', back_populates='game', foreign_keys=['Player.players_id'])

    owner_id = db.Column(db.Integer, db.ForeignKey('player.id', use_alter=True, name='fk_owner_id'))
    owner = db.relationship('Player', foreign_keys=owner_id, post_update=True)
    
    # set the teams under games
    teams = db.relationship('Team', backref='game')

    def to_json(self):
        return {
                'id': self.id,
                'name': self.name
                }

    @staticmethod
    def games_to_json():
        games = Game.query.all()
        games_dict = { 'games': [] 	}
        for game in games:
            games_dict['games'].append(game.to_json())
        return games_dict

    @staticmethod
    def by_id(gameid):
        return Game.query.filter_by(id=gameid).first()		

    @classmethod
    def new_game(cls, creator, name=""):

        Game.counter += 1

        if not name:
            name = "game" + str(Game.counter)

        game = cls(name=name, owner=[creator])

        db.session.add(game)
        db.session.commit()

        return game

    def __repr__(self):
        return f"Game {self.name} with players {self.players} and teams {self.teams}"


class Player(db.Model):

    # __tablename__ = 'left'  


    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    name = db.Column(db.String(30), unique=False, nullable=False)

    # team relationships
    team_id = db.Column(db.Integer,db.ForeignKey('team.id'), nullable=True)    

    # each game has multiple players
    # game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    # game = db.relationship("Game", back_populates="players", foreign_keys=[game_id])

    # # each player own multiple games
    # owned_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    # owned_games = db.relationship("Game", back_populates="owner", foreign_keys=[owned_id])

    player_id = db.Column(db.Integer, db.ForeignKey(Game.id))

    # product gallery many-to-one
    game = db.relationship(Game, foreign_keys=player_id, backref='players')


    def __init__(self, name="", **kwargs):
        if not name:
            name = "anonymous"

        kwargs['name'] = name
        super().__init__(**kwargs)

        db.session.add(self)
        db.session.commit()

    def to_json(self):
        return { 'player': {
                            'id': self.id,
                            'name': self.name
                            }
                }

    @staticmethod
    def players_to_json():
        players = Player.query.all()
        pdict = {'players': []}
        for player in players:
            pdict['players'].append(player.to_json())

        return pdict

    @staticmethod
    def by_id(playerid):
        return Player.query.filter_by(id=playerid).first()



 	
    def auth(self, pid, hash_val):
        """Check if the hash corresponds to the given id
        	(At the moment hash = player id
        """
        player = Player.query.filter_by(id=hash_val).first()
        if player is not None:
            return player.id == pid
        else:
            return False



    def __repr__(self):
        return f"Player {self.name}"





class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    name = db.Column(db.String(30), unique=False, nullable=False)
    
    players = db.relationship('Player', backref='team', lazy=True) 

    # each team is under a single game
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)


    @classmethod
    def new_team(cls, game, owner, name=""):

        name = name if name else "new_team"
        team = cls(name=name, game=game, owner=owner, players=[owner])
        
        db.session.add(team)
        db.session.commit()

        return team


    def to_json(self):
        team_dict = {'team': {
                            'id': self.id,
                            'name': self.name,
                            'owner': self.owner.to_json(),
                            'players': []
                        }}
        for player in self.players:
            team_dict['team']['players'].append(player.to_json())

        return team_dict

    @staticmethod
    def teams_to_json(gameid=None): 
        teams = Team.query
        if gameid is None:
            teams = teams.all()
        else:
            game = Game.query.filter_by(id=gameid).first()
            if game is not None:
                teams = teams.filter_by(game=game).all()
            else: 
                teams = []

        team_dict = {'teams': []}
        for team in teams:
            team_dict['teams'].append(team.to_json())

        return team_dict

    def __repr__(self):
        return f"Team {self.name}"




@app.route("/games", methods=['GET', 'POST'])
def games():

	if request.method == 'GET':				
		return jsonify(Game.games_to_json()) 

	if request.method == 'POST':
		pjson = request.get_json()
		player = pjson.get('player')
		print(f"player: {player}")
		if player is not None:
			if player.get('id') is not None:
				db_player = Player.query.filter_by(id=player.get('id')).first()
				if db_player is not None:
					game = Game.new_game(db_player)
					return jsonify({
									'game': {
												'id':game.id,
												'url': url_for('game', id=game.id)
												}								
									})

	return jsonify(''), UNPROCESSABLE


@app.route("/games/game<id>", methods=['PATCH', 'DELETE'])
def game(id):
	
	# owner can update game name 
	if request.method == 'PATCH':
		pass

	# owner can delete the game
	if request.method == 'DELETE':
		pass

@app.route("/games/game<gameid>/teams", methods=['GET', 'POST'])
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

        # create team        
        if player is not None and game is not None:
            team = Team.new_team(game, player, name=team_name)
            return jsonify(team.to_json())
        else:
            return jsonify(''), UNPROCESSABLE


    # get the teams
    if request.method == 'GET':             
        return jsonify(Team.teams_to_json(gameid=gameid))

@app.route("/games/game<gameid>/teams/team<teamid>", methods=['PATCH'])
def team(gameid, teamid):

	# add a player to the team
	if request.method == 'PATCH':
		pass


@app.route("/players", methods=['GET', 'POST'])
def players():

	# just for debugging get all the players
	if request.method == 'GET':
		return jsonify(Player.players_to_json()) 
	
	if request.method == 'POST':
		pjson = request.get_json()
		name = ""
		player = pjson.get('player')
		if player:
			pname = player.get('name')
			name = pname if pname else name

		player = Player(name=name)

		return jsonify(player.to_json())

	# after disconnecting
	if request.method == 'DELETE':
		pass

@app.route("/players/player<playerid>", methods=['PATCH'])
def player(playerid):

	rjson = request.get_json()

	# player can update their name
	if request.method == 'PATCH':
		phash = get_from_dict(rjson, ['player', 'hash'])
		new_name = get_from_dict(rjson, ['player', 'name'])

		# update requires player hash corresponding 
		# to the playerid and the new name
		if phash is not None and new_name is not None:
			if Player.auth(playerid, phash):
				Player.query.filter_by(id=playerid).first().update_name(new_name)
			else:
				return jsonify(''), UNAUTHORIZED
		else:
			return jsonify(''), UNPROCESSABLE












