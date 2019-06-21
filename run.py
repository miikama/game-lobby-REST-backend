

from krokeapp import app,db
from krokeapp.database import fill_database, init_database

if __name__ == "__main__":


	import argparse

	parser = argparse.ArgumentParser(description='Run the server')	
	parser.add_argument('--init_db', action='store_true',                  
	                    help='Initialize database')	
	parser.add_argument('--init_data', action='store_true',	                    
	                    help='Initialize database with dummy data')
	args = parser.parse_args()
	
	if args.init_db:
		init_database(db)

	if args.init_data:
		fill_database(db)

	app.run()