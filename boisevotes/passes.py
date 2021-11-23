from flask import Blueprint
from .PyPKPass import PKStoreCard

bp = Blueprint('passes', __name__, url_prefix='/boisevotes/passkit')

@bp.route("/")
def text_area():
  demoPass = PKStoreCard("pass.com.example.myExamplePass", "123456")
  demoPass.addPrimaryField("origin", "San Francisco", "SFO")
  demoPass.addPrimaryField("destination", "London", "LHR")
  demoPass.sign("/Users/me/Desktop/cert.p12", "passwd", "/Users/me/Desktop/demoPass.pkpass")
  return demoPass.serialized()