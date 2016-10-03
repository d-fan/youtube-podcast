#!/usr/bin/python

from server import Channel, Podcast, db_session, config, init_db

if __name__ == "__main__":
	init_db()
	channel_list = config["channels"]
	for channel_name in channel_list:
		channel = Channel.query.filter(Channel.name == channel_name).first()
		if not channel:
			channel = Channel(channel_name)
			db_session.add(channel)
			db_session.commit()
		channel.load()
		# for video_id in channel.videos:
		# 	podcast = Podcast(video_id, channel.channel_id)
		# 	print podcast
		video_id = channel.videos[0]
		podcast = Podcast.query.filter(Podcast.video_id == video_id).first()
		if not podcast:
			podcast = Podcast(video_id, channel.channel_id)
			db_session.add(channel)
			db_session.commit()
		podcast.download()
