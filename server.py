#!/usr/bin/python

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from jinja2 import Template
import yaml

###################
# App
###################

app = Flask(__name__)

config = {}

def LoadConfig(file_name):
    global config
    with open(file_name, "r") as input_file:
        config = yaml.load(input_file)
        print "Config load successful"
        return
    print "Failed to load config"
    exit()
LoadConfig("config.yml")

###################
# Database
###################

engine = create_engine('sqlite:///podcast.db', convert_unicode=True)
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

from apiclient.discovery import build
from datetime import timedelta
from dateutil import parser
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
import pafy
import re
import os

class Channel(Base):
    __tablename__ = 'channels'

    id = Column(Integer, primary_key=True)
    name = Column(Text(), unique=True)
    image = Column(Text())
    channel_id = Column(Text())
    description = Column(Text())

    def __init__(self, name):
        self.name = name
        self.channel_id = None

    def load(self):
        service = build('youtube', 'v3', developerKey=config['key'])
        self.videos = []

        # Get id
        kwargs = {
            'part': 'id',
            'forUsername': self.name
        }
        response = service.channels().list(**kwargs).execute()
        if len(response['items']) == 1:
            self.channel_id = response['items'][0]['id']
        else:
            raise Exception("Could not get id for channel %s" % self.name)
            return

        # Get videos
        kwargs = {
            'order': 'date',
            'part': 'id',
            'channelId': self.channel_id,
            'maxResults': 50,
        }
        response = service.search().list(**kwargs).execute()
        for item in response['items']:
            if item['id']['kind'] == u'youtube#video':
                self.videos.append(item['id']['videoId'])
        return self

    def __repr__(self):
        return '<Channel %s; id %s>' % (self.name, self.channel_id)

class Podcast(Base):
    __tablename__ = 'podcasts'

    id = Column(Integer, primary_key=True)
    video_id = Column(String(11), unique=True)
    ready = Column(Boolean())
    
    title = Column(Text())
    description = Column(Text())
    channel_name = Column(Text())
    date = Column(DateTime())
    file_path = Column(Text())
    thumbnail = Column(Text())
    length = Column(Text())
    size = Column(Text())

    def __init__(self, video_id, channel_id):
        self.ready = False
        self.channel_name = channel_id
        self.video_id = video_id
        self.video_obj = pafy.new(self.video_id)
        self.audio_obj = self.video_obj.getbestaudio()
        self.thumb_url = self.video_obj.thumb
    
        self.size = self.audio_obj.get_filesize()
        self.date = parser.parse(self.video_obj.published)
        self.title = self.video_obj.title
        self.length = self.video_obj.duration
        self.file_path = "%s/%s.%s" % (channel_id, video_id, self.audio_obj.extension)
        self.thumbnail = "%s/%s.jpg" % (channel_id, video_id)
        self.description = self.video_obj.description.replace("\n", "<br/>")

    def download(self):
        if self.ready:
            return

        # Create download directory if it doesn't already exist
        if not os.path.exists(os.path.dirname(self.file_path)):
            try:
                os.makedirs(os.path.dirname(self.file_path))
            except Exception as e:
                print e

        def mark_ready(bytes_total, bytes_downloaded, progress, rate, eta):
            """Mark this object as ready once the file is downloaded."""
            if bytes_downloaded < bytes_total:
                return
            print "Done downloading %s" % str(self)
            self.ready = True
            db_session.add(self)
            db_session.commit()
            return

        self.audio_obj.download(
            filepath = self.file_path,
            quiet = True,
            callback = mark_ready)
        pass

    def __repr__(self):
        return '<Podcast %s>' % self.title

###################
# Views
###################

from flask import Response, abort, send_from_directory
from datetime import datetime

feed_template = Template("""<rss
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:content="http://purl.org/rss/1.0/modules/content/"
    xmlns:atom="http://www.w3.org/2005/Atom"
    xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
    xmlns:media="http://search.yahoo.com/mrss/"
    version="2.0">
    <channel>
        <title>{{ name }}</title>
        <description>{{ description }}</description>
        <language>en-us</language>
        <lastBuildDate>{{ now }}</lastBuildDate>
        <itunes:explicit>no</itunes:explicit>
        <media:copyright>{{ name }}</media:copyright>
        <media:thumbnail url="{{ image }}" />
        <itunes:author>{{ name }}</itunes:author>
        <itunes:image href="{{ image }}" />
        <itunes:subtitle>{{ description }}</itunes:subtitle>
        <itunes:summary>{{ description }}</itunes:summary>
        {{ items }}
        <copyright>{{ name }}</copyright>
        <media:credit role="author">{{ name }}</media:credit>
        <media:rating>nonadult</media:rating>
    </channel>
</rss>
""")

episode_template = Template("""
<item>
    <title>{{ title }}</title>
    <description><![CDATA[{{ description }}]]></description>
    <pubDate>{{ date }}</pubDate>
    <media:content url="http://192.168.0.100:5000/{{ file_path }}" type="audio/mpeg" />
    <media:description type="plain">{{ title }}</media:description>
    <itunes:duration>{{ length }}</itunes:duration>
    <itunes:summary><![CDATA[{{ description }}]]></itunes:summary>
    <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">{{ channel_name }}</dc:creator>
    <itunes:explicit>no</itunes:explicit>
    <itunes:subtitle><![CDATA[{{ description }}]]></itunes:subtitle>
    <itunes:author>{{ channel_name }}</itunes:author>
    <enclosure url="http://192.168.0.100:5000/{{ file_path }}" length="0" type="audio/mpeg" />
</item>
""")

class misc:
    pass

@app.route("/<channel_name>")
def get_podcasts(channel_name):
    print "Retrieving %s" % channel_name
    channel = Channel.query.filter(Channel.name == channel_name).first()
    if not channel:
        abort(404) 
    channel.items = ''
    channel.now = str(datetime.now())
    podcast_list = Podcast.query.filter(Podcast.channel_name == channel.channel_id)
    for podcast in podcast_list:
        channel.items += episode_template.render(podcast.__dict__)
    feed = feed_template.render(channel.__dict__)
    return Response(feed, mimetype='text/xml')

@app.route('/<path:path>')
def send_media(path):
    return send_from_directory('.', path)

###################
# Main
###################
if __name__ == "__main__":
    limit = timedelta(days = 30)
    app.run(host='0.0.0.0')
