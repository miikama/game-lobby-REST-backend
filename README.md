


/players 
	
	- POST
		* on startup, return player id 
	- DELETE
		* with player id 


/players/player<playerid>
	- PATCH 
		* change name

/games

	- POST
		* create new game
		* needs player id who is the owner of the game
		* return game id	
	- GET
		* list all the games
		* returns id and name


/games/game<gameid>
	

/games/game<gameid>/teams


/games/game<gameid>/teams/team<teamid>



```json
{
	'games' : 
}

```