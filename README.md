# Boise Elections Software

Boise High Election software is a free and open-source Flask plugin made to assist with School Elections. Implementation of the app is simple and can be done with just a couple lines of code.

## Example Code

Here's an example of how to plug in the software to your existing Flask app:
```python

from flask import Flask
from boisevotes import BoiseElectionsSoftware

app = Flask(__name__)
app.secret_key = ""
app.config["ELECTION_GOOGLE_CLIENT_ID"] = ""
app.config["ELECTION_GOOGLE_CLIENT_SECRET"] = ""
# install the plugin here
election = BoiseElectionsSoftware(app)

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=8080)

```

## Setup

### MongoDB

- `ELECTION_DB_URL`


### Sign In With Google

- `ELECTION_GOOGLE_CLIENT_ID`
- `ELECTION_GOOGLE_CLIENT_SECRET`