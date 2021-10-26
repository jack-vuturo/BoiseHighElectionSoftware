from flask import Blueprint, Flask, current_app
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

class BoiseElectionsSoftware:
	bp = Blueprint("boise_votes", __name__, static_folder="/boisevotes/static", template_folder="/boisevotes/templates")
	GOOGLE_CLIENT_SECRET = ""
	GOOGLE_DISCOVERY_URL = ("https://accounts.google.com/.well-known/openid-configuration")
	login_manager = LoginManager()
	client = None

	def __init__(self, app: Flask):
		self.GOOGLE_CLIENT_ID = app.config["ELECTION_GOOGLE_CLIENT_ID"]
		self.GOOGLE_CLIENT_SECRET = app.config["ELECTION_GOOGLE_CLIENT_SECRET"]
		self.login_manager.init_app(app)
		self.client = WebApplicationClient(self.GOOGLE_CLIENT_ID)
		app.register_blueprint(self.bp)

	@login_manager.user_loader
	def load_user(user_id):
			return ""

	@bp.route("/")
	def index():
		return """
		<h1>Hello :)</h1>
		"""