import datetime
from typing import Optional
from flask import abort
from mongoengine import connect, Document, StringField, ReferenceField, EmbeddedDocument, EmbeddedDocumentListField, DictField, ListField, IntField, DateTimeField, Q
from bson import ObjectId
from flask_login import UserMixin

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
  
  class BallotVariation(Document):
    name = StringField(max_length=120)
    races = ListField(ReferenceField("BallotVariation"))
  
  class BallotSection(EmbeddedDocument):
    race = ReferenceField('Race')
    votes = DictField()
  
  class Ballot(Document):
    variation = ReferenceField('BallotVariation')
    assignedTo = ReferenceField('User', required=False)
    sections = EmbeddedDocumentListField("BallotSection")
  
  class Election(Document):
    name = StringField(max_length=120)
    owner = ReferenceField('User')
    starts = DateTimeField()
    ends = DateTimeField()
    managers = ListField(ReferenceField('User'))
    voter_emails = ListField(StringField())
    races = ListField(ReferenceField('Race'))
    ballot_variations = ListField(ReferenceField('BallotVariation'))
    ballots = ListField(ReferenceField('Ballot'))

    @property
    def pk_str(self):
      return str(self.pk)

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
      if user.pk in self.managers or user == self.owner:
        if status == "Registered":
          status += ", "
        else:
          status = ""
        if user.pk in self.managers:
          status += "Manager"
        elif user == self.owner:
          status += "Owner"
      return status