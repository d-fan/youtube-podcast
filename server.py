#!/usr/bin/python

from flask import Flask
from flask_alchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

class Podcast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text())
    description = db.Column(db.Text())
    pubDate = db.Column(db.DateTime())

    media_content = db.Column(db.Text())
    itunes_duration = db.Column(db.Text())

    itunes_author = db.Column(db.Text())

    def __init__(self, initDict):
        self.title = initDict.get('title', 'No Title')
        self.description = initDict.get('description', 'No description.')
        self.pubDate =
        self.media_content = initDict.get('media_content')
        self.itunes_duration = initDict.get('itunes_duration', '00:00')
        self.itunes_author = initDict.get('itunes_author', 'No Author')

    def __repr__(self):
        return '<Podcast %s>' % self.title
