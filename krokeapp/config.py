


class Config:

	secret_key = '3456789098765434567890098765456787664781648769615696287'
	database_uri = "sqlite:///site.db"


	def update_app_config(self, app):

		app.config['SECRET_KEY'] = self.secret_key
		app.config['SQLALCHEMY_DATABASE_URI'] = self.database_uri
	 