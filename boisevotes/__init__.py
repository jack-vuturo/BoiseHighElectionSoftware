import datetime
from flask import Blueprint, Flask, redirect, url_for, session, request, render_template, abort, jsonify, flash
from functools import wraps
from oauthlib.oauth2 import WebApplicationClient
from .oauth import GoogleSignIn
from .db import BoiseElectionsDatabase, pk, Q
from .passes import bp as passes_bp

class BoiseElectionsSoftware:
  bp = Blueprint("boisevotes", __name__, url_prefix = "/vote", static_folder="election_static", template_folder="election_templates")
  bp.register_blueprint(passes_bp)
  GOOGLE_CLIENT_ID = None
  GOOGLE_CLIENT_SECRET = None
  GOOGLE_DISCOVERY_URL = "https://accounts.google.com/o/oauth2/v2/auth"
  db = None
  client = None

  def __init__(self, app: Flask):
    self.GOOGLE_CLIENT_ID = app.config["ELECTION_GOOGLE_CLIENT_ID"]
    self.GOOGLE_CLIENT_SECRET = app.config["ELECTION_GOOGLE_CLIENT_SECRET"]
    self.client = WebApplicationClient(self.GOOGLE_CLIENT_ID)
    self.db = BoiseElectionsDatabase(app.config["ELECTION_DATABASE_HOST"])
    self.add_routes()
    app.register_blueprint(self.bp)
  
  def login_required(self, f):
    @wraps(f)
    def wrapper(*args, **kwargs):
      id = session.get("user_id", None)
      if id is None:
        return redirect(url_for('boisevotes.login', next=request.url))
      user = self.db.User.objects(user_id=id).first()
      if not user:
        session.clear()
        return redirect(url_for('boisevotes.login', next=request.url))
      else:
        return f(user, *args, **kwargs)
    return wrapper 
  
  def check_user_is(self, position, election, user):
    if position == "admin":
      if not election.is_admin(user):
        return abort(401)
    elif position == "voter":
      if user.email not in election.voter_emails:
        return abort(401)
    else:
      pass
  
  def assign_ballot(self, election, ballot, user):
    if user.email not in election.voter_emails:
      raise Exception("user not registered")
    if election.has_voted(user):
      raise Exception("user has already voted")
    ballot.assigned_to = user
    ballot.save()
    election.ballots.append(ballot)
    election.save()
  
  def add_routes(self):

    @self.bp.route("/")
    def landing():
      return render_template("landing.html")

    @self.bp.route("/login")
    def login():
      if session.get("user_id", None) != None:
        return redirect(url_for("boisevotes.elections"))
      next_page = request.args.get("next", None)
      print(next_page)
      if next_page != None:
        session["login_next_page"] = next_page
        return redirect(url_for("boisevotes.login"))
      return render_template("login.html")
    
    @self.bp.route("/login/siwg")
    def google_login():
      if session.get("user_id", None) != None:
        return redirect(url_for("boisevotes.elections"))
      return GoogleSignIn(self.GOOGLE_CLIENT_ID, self.GOOGLE_CLIENT_SECRET).authorize()

    @self.bp.route("/login/callback")
    def callback():
      last, first, email, pic, id = GoogleSignIn(self.GOOGLE_CLIENT_ID, self.GOOGLE_CLIENT_SECRET).callback()
      user = self.db.User.objects(user_id=id).first()
      if not user:
        user = self.db.User(user_id=id, name=f"{first} {last}", email=email, profile_pic=pic).save()
      session["user_id"] = user.user_id
      next_page = session.get("login_next_page", None)
      print(next_page)
      if next_page != None:
        session["login_next_page"] = None
        return redirect(next_page)
      else:
        return redirect(url_for("boisevotes.elections"))
    
    @self.bp.route("/logout")
    @self.login_required
    def logout(user):
      session.clear()
      return redirect(url_for("boisevotes.login"))
    
    @self.bp.route("/pass")
    @self.login_required
    def fastpass(user):
      return render_template("fastpass.html", user=user, fastpass=True)
    
    @self.bp.route("/elections")
    @self.login_required
    def elections(user):
      elections = self.db.Election.objects(
        Q(owner = user) |
        Q(managers = user) |
        Q(voter_emails = user.email)
      )
      return render_template("elections.html", user=user, elections=elections)
    
    @self.bp.route("/election/new")
    @self.login_required
    def new_election(user):
      election = self.db.Election(
        name="Untitled Election",
        owner=user,
        starts=datetime.datetime.now(),
        ends=datetime.datetime.now(),
        managers=[],
        races = [],
        voter_emails = [],
        ballots=[]
      )
      election.save()
      return redirect(url_for('boisevotes.edit_election', election_id=str(election.pk)))
    
    @self.bp.route("/election/<string:election_id>/edit", methods=["GET", "POST"])
    @self.login_required
    def edit_election(user, election_id):
      election = self.db.Election.objects(pk=pk(election_id)).first()
      if election == None:
        abort(404)
      self.check_user_is("admin", election, user)
      if request.method == "GET":
        return render_template("edit_election.html", user=user, election=election)
      elif request.method == "POST":
        election.name = request.form.get("election-name", "Untitled Election")
        election.save_dates(
          request.form.get("start-datetime", ""),
          request.form.get("end-datetime", "")
        )
        election.save()
        return redirect(url_for("boisevotes.elections"))
      else:
        abort(404)
    
    @self.bp.route("/election/<string:election_id>/race/new", methods=["GET", "POST"])
    @self.login_required
    def new_race(user, election_id):
      election = self.db.Election.objects(pk=pk(election_id)).first()
      self.check_user_is("admin", election, user)
      race = self.db.Race(
        name = "Untitled Race",
        votes = 1,
        canidates = ["Person :)"]
      )
      race.save()
      election.races.append(race)
      election.save()
      return redirect(url_for('boisevotes.edit_race', election_id=str(election.pk), race_id=str(race.pk)))
    
    @self.bp.route("/election/<string:election_id>/race/<string:race_id>/edit", methods=["GET", "POST"])
    @self.login_required
    def edit_race(user, election_id, race_id):
      election = self.db.Election.objects(pk=pk(election_id)).first()
      race = self.db.Race.objects(pk=pk(race_id)).first()
      if election == None or race == None:
        abort(404)
      self.check_user_is("admin", election, user)
      if request.method == "GET":
        return render_template("edit_race.html", user=user, election=election, race=race)
      elif request.method == "POST":
        race.name = request.form.get("race-name", "")
        race.votes = request.form.get("race-votes", 1)
        race.canidates = list(filter(lambda val: val != "", request.form.getlist('canidates[]')))
        race.save()
        return redirect(url_for('boisevotes.edit_election', election_id=str(election.pk)))
      else:
        abort(400)
    
    @self.bp.route("/election/<string:election_id>/vote", methods=["GET", "POST"])
    @self.login_required
    def online_ballot(user, election_id):
      election = self.db.Election.objects(pk=pk(election_id)).first()
      if election == None:
        abort(404)
      self.check_user_is("voter", election, user)
      if request.method == "GET":
        if election.has_voted(user):
          flash("You have already voted", "info")
          return redirect(url_for("boisevotes.elections"))
        return render_template("online_ballot.html", user=user, election=election)
      elif request.method == "POST":
        ballot = self.db.Ballot()
        self.assign_ballot(election, ballot, user)
        data = {}
        for race in election.races:
          vote = {}
          for i in range(1, race.votes + 1):
            vote[str(i)] = request.form[f"{race.pk}op{i}"]
          data[str(race.pk)] = vote
        ballot.data = data
        ballot.save()
        return redirect(url_for("boisevotes.elections"))
      
    @self.bp.route("/election/<string:election_id>/dashboard")
    @self.login_required
    def election_dashboard(user, election_id):
      return redirect(url_for("boisevotes.election_overview", election_id=election_id))
      
    @self.bp.route("/election/<string:election_id>/dashboard/overview")
    @self.login_required
    def election_overview(user, election_id):
      election = self.db.Election.objects(pk=pk(election_id)).first()
      if election == None:
        abort(404)
      self.check_user_is("admin", election, user)
      return render_template("dash_overview.html", user=user, election=election)
    
    @self.bp.route("/election/<string:election_id>/dashboard/register", methods=["GET", "POST"])
    @self.login_required
    def election_register(user, election_id):
      election = self.db.Election.objects(pk=pk(election_id)).first()
      if election == None:
        abort(404)
      self.check_user_is("admin", election, user)
      if request.method == "GET":
        return render_template("dash_register.html", user=user, election=election)
      elif request.method == "POST":
        election.voter_emails = list(filter(lambda val: val != "", request.form.getlist('email[]')))
        election.save()
        return redirect(url_for("boisevotes.election_overview", election_id=election.id))
    
    @self.bp.route("/election/<string:election_id>/dashboard/checkin", methods=["GET", "POST"])
    @self.login_required
    def election_check_in(user, election_id):
      election = self.db.Election.objects(pk=pk(election_id)).first()
      if election == None:
        abort(404)
      self.check_user_is("admin", election, user)
      if request.method == "GET":
        return render_template("dash_check_in.html", user=user, election=election)
      else:
        return jsonify(voters=election.voter_emails)
    
    @self.bp.route("/election/<string:election_id>/dashboard/scan")
    @self.login_required
    def election_scanner(user, election_id):
      election = self.db.Election.objects(pk=pk(election_id)).first()
      if election == None:
        abort(404)
      self.check_user_is("admin", election, user)
      return render_template("dash_scan.html", user=user, election=election)
    
    @self.bp.route("/election/<string:election_id>/dashboard/results")
    @self.login_required
    def election_results(user, election_id):
      election = self.db.Election.objects(pk=pk(election_id)).first()
      if election == None:
        abort(404)
      self.check_user_is("admin", election, user)
      charts = election.winner_chart_data()
      return render_template("dash_results.html", user=user, election=election, charts=charts)