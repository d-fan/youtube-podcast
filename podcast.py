#!/usr/bin/python

from apiclient.discovery import build
import json
import pprint
import pafy
import re
import yaml

config = {}

class Channel:
    def __init__(self, name):
        self.service = build('youtube', 'v3', developerKey=config['key'])
        self.name = name
        self.id = None
        self.videos = []
        self.ready = False

    def load(self):
        # Get id
        kwargs = {
            'part': 'id',
            'forUsername': self.name
        }
        response = self.service.channels().list(**kwargs).execute()
        if len(response['items']) == 1:
            self.id = response['items'][0]['id']
        else:
            print "Error: Could not get id for channel %s" % self.name
            return

        # Get videos
        kwargs = {
            'order': 'date',
            'part': 'id',
            'channelId': self.id,
            'maxResults': 25,
        }
        response = self.service.search().list(**kwargs).execute()
        for item in response['items']:
            pprint.pprint(item)
            if item['id']['kind'] == u'youtube#video':
                self.videos.append(item['id']['videoId'])
        return self


def LoadConfig(file_name):
    global config
    with open(file_name, "r") as input_file:
        config = yaml.load(input_file)
        print "Config load successful"
        return
    print "Failed to load config"
    exit()
    
if __name__ == "__main__":
    LoadConfig("config.yml")
    for channel_name in config['channels']:
        channel = Channel(channel_name)
        channel.load()
        for video_id in channel.videos:
            path = "media/%s/%s" % (channel_name, video_id)
            video = pafy.new(video_id)
            video.getbestaudio().download(filepath=path)
