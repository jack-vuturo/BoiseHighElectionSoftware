import datetime
from typing import Optional
from flask import abort
from mongoengine import connect, Document, StringField, ReferenceField, DictField, ListField, IntField, DateTimeField, Q
from bson import ObjectId
from flask_login import UserMixin
import pyrankvote
from .charts import ChartJS, ChartDataSet
from pyrankvote import Ballot as RVBallot
from pyrankvote import Candidate as RVCandidate

def pk(string: str) -> Optional[ObjectId]:
  try:
    return ObjectId(string)
  except:
    abort(404)

def query(**query) -> Q:
  return Q(query)

class BoiseElectionsDatabase:
  
  def __init__(self, host_url):
    connect(host=host_url)

  class User(Document, UserMixin):
    user_id = StringField(max_length=120, required=True)
    name = StringField(max_length=120, required=True)
    email = StringField(max_length=120, required=True)
    profile_pic = StringField(max_length=400, required=True)
  
  class Race(Document):
    name = StringField(max_length=120)
    votes = IntField(min_value=1, max_value=5)
    canidates = ListField(StringField(unique=True))

    @property
    def pk_str(self):
      return str(self.pk)
  
  class Ballot(Document):
    assigned_to = ReferenceField('User', required=False)
    data = DictField(required=False)
  
  class Election(Document):
    name = StringField(max_length=120)
    owner = ReferenceField('User')
    starts = DateTimeField()
    ends = DateTimeField()
    managers = ListField(ReferenceField('User'))
    voter_emails = ListField(StringField())
    races = ListField(ReferenceField('Race'))
    ballots = ListField(ReferenceField('Ballot'))

    @property
    def pk_str(self):
      return str(self.pk)
    
    @property
    def races_by_id(self):
      return {str(race.pk): race for race in self.races}

    @property
    def html_start_date(self):
      return self.starts.strftime("%Y-%m-%dT%H:%M")
    
    @property
    def html_end_date(self):
      return self.ends.strftime("%Y-%m-%dT%H:%M")
    
    @property
    def readable_start_date(self):
      return self.starts.strftime("%b %d, %y %I:%M%p")
    
    @property
    def readable_end_date(self):
      return self.ends.strftime("%b %d, %y %I:%M%p")
    
    def save_start_date(self, date):
      try:
        self.starts = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M')
      except:
        pass
    
    def save_end_date(self, date):
      try:
        self.ends = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M')
      except:
        pass
    
    def save_dates(self, start, end):
      self.save_start_date(start)
      self.save_end_date(end)
    
    def get_user_status(self, user) -> str:
      status = "Not Registered"
      if user.email in self.voter_emails:
        status = "Registered"
        if self.has_voted:
          status = "Voted"
      if user.pk in self.managers or user == self.owner:
        if status != "Not Registered":
          status += ", "
        else:
          status = ""
        if user.pk in self.managers:
          status += "Manager"
        elif user == self.owner:
          status += "Owner"
      return status
    
    def is_admin(self, user):
      if user == self.owner:
        return True
      elif user.pk in self.managers:
        return True
      else:
        return False
    
    def is_voter(self, user):
      return user.email in self.voter_emails
    
    def has_voted(self, user):
      print("has voted:", self.ballots)
      return user.pk in [ballot.assigned_to.pk for ballot in self.ballots]
    
    def calc_winners(self):
      data = {}
      for race in self.races:
        race_data = { 
          "candidates": { name : RVCandidate(name) for name in race.canidates },
          "ballots": []
        }
        data[str(race.pk)] = race_data
      for ballot in self.ballots:
        for race in self.races:
          race_data = ballot.data.get(str(race.pk), None)
          race_votes = []
          if race_data == None:
            continue
          for x in range(1, race.votes + 1):
            name = race_data.get(str(x), None)
            if name != None:
              race_votes.append(data[str(race.pk)]["candidates"][name])
          data[str(race.pk)]["ballots"].append(RVBallot(ranked_candidates=race_votes))
          data[str(race.pk)]["result"] = pyrankvote.instant_runoff_voting(data[str(race.pk)]["candidates"].values(), data[str(race.pk)]["ballots"])
      return {race_id: race_data["result"] for race_id, race_data in data.items()}
    
    def winner_chart_data(self):
      COLORS = ["Tomato", "Orange", "MediumSeaGreen"]
      data = self.calc_winners()
      charts = []
      for race_id, race_tally in data.items():
        race_data = self.races_by_id[race_id]
        chart = ChartJS(race_id, race_data.name, "line")
        new_chart_data = {c : ChartDataSet(c, COLORS[1], [0]) for c in race_data.canidates}
        chart.labels = [f"Round {x}" for x in range(0, len(race_tally.rounds))]
        chart.labels.append("Final Round")
        for x in range(len(race_tally.rounds)):
          round = race_tally.rounds[x]
          for cr in round.candidate_results:
            if str(cr.status) == "Hopeful":
              new_chart_data[cr.candidate.name].data.append(cr.number_of_votes)
            elif str(cr.status) == "Elected":
              new_chart_data[cr.candidate.name].data.append(cr.number_of_votes)
              new_chart_data[cr.candidate.name].color = COLORS[2]
            elif x != len(race_tally.rounds) - 1:
              new_chart_data[cr.candidate.name].color = COLORS[0]
        chart.data = new_chart_data.values()
        charts.append(chart)
      return charts
