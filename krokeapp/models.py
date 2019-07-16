

from datetime import datetime

from flask import url_for

from krokeapp import db


class Game(db.Model):
    # __tablename__ = 'right'

    counter = 0

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    name = db.Column(db.String(30), unique=False, nullable=False)

    owner_id = db.Column(db.Integer, db.ForeignKey('player.id', use_alter=True, name='fk_owner_id'))
    owner = db.relationship('Player', foreign_keys=owner_id, post_update=True)
    
    # set the teams under games
    teams = db.relationship('Team', backref='game')

    def to_json(self):
        game_json ={
                'game': {                   
                        'id': self.id,
                        'name': self.name,
                        'url': url_for('api.game', id=self.id),
                        'owner': self.owner.to_json(),
                        'players' : []        
                        }
                }
        # add the players
        for player in self.players:
            game_json['game']['players'].append(player.to_json())

        return game_json

    def add_player(self, player):
        """
            Return whether player addition was succesful
        """        
        if player is None:
            return False
        
        self.players.append(player)        
        db.session.commit()

    @staticmethod
    def remove_game(game):      
        """
            All the teams under the game are considered 
            the games property and are removed as well.
        """          
        for team in game.teams:
            db.session.delete(team)
        db.session.delete(game)
        db.session.commit()

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

        game = cls(name=name, owner=creator)

        db.session.add(game)
        db.session.commit()

        return game

    def __repr__(self):
        return f"Game {self.name} with players {self.players} and teams {self.teams}"





class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    name = db.Column(db.String(30), unique=False, nullable=False)
    
    # each team is under a single game
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)

    # one-to-one map
    owner_id = db.Column(db.Integer, db.ForeignKey('player.id', use_alter=True, name='fk_team_owner_id'))
    owner = db.relationship('Player', foreign_keys=owner_id, post_update=True)


    @classmethod
    def new_team(cls, game, owner, name=""):
        name = name if name else "new_team"
        team = cls(name=name, game=game, owner=owner)
        
        db.session.add(team)
        db.session.commit()

        return team
    
    def add_player(self, player):
        """
            Return whether player addition was succesful
        """        
        if player is None:
            raise RuntimeError('player argument not defined')

        self.players.append(player)
        db.session.commit()


    def to_json(self):
        team_dict = {'team': {
                            'id': self.id,
                            'name': self.name,
                            'url': url_for('api.team', gameid=self.game.id, teamid=self.id),
                            'owner': self.owner.to_json(),
                            'players': []
                        }}
        for player in self.players:
            team_dict['team']['players'].append(player.to_json())

        return team_dict

    @staticmethod
    def remove_team(team):
        db.session.delete(team)
        db.session.commit()

    @staticmethod
    def by_id(teamid):
        return Team.query.filter_by(id=teamid).first()

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




class Player(db.Model):

    # __tablename__ = 'left'  


    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    name = db.Column(db.String(30), unique=False, nullable=False)

    # a foreign key for the Team owner relationship
    team_id = db.Column(db.Integer, db.ForeignKey(Team.id))

    # player team many-to-one
    team = db.relationship(Team, foreign_keys=team_id, backref='players')

    # a foreign key for the Game owner relationship
    game_id = db.Column(db.Integer, db.ForeignKey(Game.id))

    # player game many-to-one
    game = db.relationship(Game, foreign_keys=game_id, backref='players')


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


    def update_name(self, new_name):
        self.name = new_name
        db.session.commit()

    def leave_team(self):        

        if self.team is not None:            
            self.team = None

        db.session.commit()
        
    def leave_game(self):

        if self.game is not None:
            self.game = None

        db.session.commit()
 	
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
