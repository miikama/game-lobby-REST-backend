


from krokeapp.routes import Game,Player,Team
from krokeapp import logger
from sqlalchemy.exc import OperationalError
import os


def init_database(database, app):	

	with app.app_context():
		database.create_all()
		database.session.commit()

def init_if_not_found(database,app):

	try:
		with app.app_context():		
			Game.query.all()
	except OperationalError:

		logger.info("Database not found")
		if app.config['AUTO_INIT_DB']:			
			logger.info("Initializing database")
			init_database(database, app)
		else:
			logger.info("Database not initialized, exiting.")

def fill_database(database, app):


	with app.app_context():
		player1 = Player(name="player1")
		player2 = Player(name="player2")
		player3 = Player(name="player3")

		game1 = Game(name="game1", owner=player1)
		game2 = Game(name="game2", owner=player3)

		team1 = Team(name="team1", game=game1, owner=player1)
		team2 = Team(name="team2", game=game1, owner=player2)
		team3 = Team(name="team3", game=game2, owner=player3)

		game1.players.append(player1)
		game1.players.append(player2)

		player1.team = team1

		database.session.add(game1)
		database.session.add(game2)

		database.session.commit()

		print(f"{game1}")
		print(f"{player1}")
		print(f"{player2}")
		print(f"{team1}")
		print(f"{team2}")



