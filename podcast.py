#!/usr/bin/python

from apiclient.discovery import build
import json
import pprint
import pafy

class YoutubePodcast:
    def __init__(self, api_key):
        self.service = build('youtube', 'v3', developerKey=api_key)

    def GetChannelIdFromChannelName(self, username):
        request = self.service.channels().list(part="id", forUsername=username)
        response = request.execute()
        if len(response['items']) != 1:
            return ''
        return response['items'][0]['id']

    def GetVideosForChannel(self, channel_id, maxResults=25):
        request = self.service.search().list(order='date', part='id', channelId=channel_id, maxResults=maxResults)
        response = request.execute()
        videos = []
        for item in response['items']:
            if item['id']['kind'] == u'youtube#video':
                videos.append(item['id']['videoId'])
        return videos


if __name__ == "__main__":
    podcast = YoutubePodcast('AIzaSyClwOKX0tQJsHdchbSjvetfWYgAazIJD8U')
    channel_id = podcast.GetChannelIdFromChannelName('BrookingsInstitution')
    videos = podcast.GetVideosForChannel(channel_id)
    video = pafy.new(videos[0])
    print video
    print video.description.encode('utf-8')
    print video.getbestaudio()
