import os
from flask import Flask
from boisevotes import BoiseElectionsSoftware

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["ELECTION_DATABASE_HOST"] = os.environ['DATABASE_HOST']
app.config["ELECTION_GOOGLE_CLIENT_ID"] = os.environ['GOOGLE_CLIENT_ID']
app.config["ELECTION_GOOGLE_CLIENT_SECRET"] = os.environ['GOOGLE_CLIENT_SECRET']
election = BoiseElectionsSoftware(app)

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=8080)