#!/usr/bin/python

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

###################
# App
###################

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

###################
# Database
###################

engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    # import yourapplication.models
    Base.metadata.create_all(bind=engine)

###################
# Teardown
###################

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

##################
# Models
###################

from sqlalchemy import Column, Integer, String, Text, DateTime

class Podcast(Base):
    __tablename__ = 'podcasts'

    id = Column(Integer, primary_key=True)
    title = Column(Text())
    description = Column(Text())
    pubDate = Column(DateTime())

    media_content = Column(Text())
    itunes_duration = Column(Text())

    itunes_author = Column(Text())

    def __init__(self, initDict):
        self.title = initDict.get('title', 'No Title')
        self.description = initDict.get('description', 'No description.')
        self.pub_date = 0
        self.media_content = initDict.get('media_content')
        self.itunes_duration = initDict.get('itunes_duration', '13:37')
        self.itunes_author = initDict.get('itunes_author', 'No Author')

    def __repr__(self):
        return '<Podcast %s>' % self.title

###################
# Main
###################
if __name__ == "__main__":
    app.run()