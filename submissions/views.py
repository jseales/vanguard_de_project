#!/usr/bin/python3

import sqlite3
from sqlalchemy import create_engine
import pprint
import pandas as pd



def make_views(views, database='spotify.db'):
	'''Creates the specified views into a database.
	views: Dict. Keys are view names. Values are SQL queries to create the views.
	database: the database in which the view should be stored.''' 
	con = sqlite3.connect(database)
	cur = con.cursor()
	for view_name, view_query in views.items():
		cur.execute("DROP VIEW IF EXISTS " + view_name + ";")
		cur.execute(view_query)



Artists_6_Longest_Songs = '''
CREATE VIEW Artists_6_Longest_Songs AS
SELECT artist_name, song_name, ROUND(song_length / 60000) song_length
FROM
	(SELECT artist_album.artist_name artist_name,
		Track.song_name song_name,
		Track.duration_ms song_length,
		RANK() OVER (PARTITION BY artist_name ORDER BY Track.duration_ms DESC,
		Track.track_id) length_rank,
		AVG(Track.duration_ms) OVER (PARTITION BY artist_name) avg_length
	FROM
		(SELECT Artist.artist_name artist_name, 
		Album.album_id album_id
		FROM Artist JOIN Album 
		ON Artist.artist_id = Album.artist_id) artist_album
		JOIN Track
		ON artist_album.album_id = Track.album_id
	ORDER BY avg_length DESC)
WHERE length_rank <= 6;'''
	  
Artists_By_Followers = '''
CREATE VIEW Artists_By_Followers AS
SELECT artist_name, followers
FROM Artist 
ORDER BY followers DESC;'''

Artists_6_Fastest_Songs = '''
CREATE VIEW Artists_6_Fastest_Songs AS
SELECT artist_name, song_name, tempo  
FROM
	(SELECT artist_song.artist_name artist_name,
		artist_song.song_name song_name,
		Track_Feature.tempo tempo,
		RANK() OVER (PARTITION BY artist_name ORDER BY Track_Feature.tempo DESC,
		Track_Feature.track_id) tempo_rank,
		AVG(Track_Feature.tempo) OVER (PARTITION BY artist_name) avg_tempo
	FROM
		(SELECT artist_album.artist_name artist_name, 
			Track.song_name song_name, 
			Track.track_id track_id
		FROM (SELECT Artist.artist_name artist_name, 
			Album.album_id album_id
			FROM Artist JOIN Album 
			ON Artist.artist_id = Album.artist_id) artist_album
		JOIN Track
		ON artist_album.album_id = Track.album_id) artist_song
	JOIN Track_Feature
	ON artist_song.track_id = Track_Feature.track_id
	ORDER BY avg_tempo DESC)
WHERE tempo_rank <= 6;'''


Artist_Happiness = '''
CREATE VIEW Artist_Happiness AS
SELECT artist_name, song_name, happiness, happy_rank
FROM
	(SELECT artist_song.artist_name artist_name,
			artist_song.song_name song_name,
			Track_feature.valence happiness,
			RANK() OVER (PARTITION BY artist_name ORDER BY 
						Track_Feature.valence DESC, artist_song.track_id) happy_rank,
			COUNT() OVER (PARTITION BY artist_name) song_count,
			avg(Track_Feature.valence) OVER (PARTITION BY artist_name) avg_happy  
	FROM
		(SELECT artist_album.artist_name artist_name, 
			Track.song_name song_name,
			Track.track_id track_id
		FROM (SELECT Artist.artist_name, Album.album_id
			FROM Artist JOIN Album 
			ON Artist.artist_id = Album.artist_id) artist_album
		JOIN Track
		ON artist_album.album_id = Track.album_id) artist_song
	JOIN Track_Feature
	ON artist_song.track_id = Track_Feature.track_id
	ORDER BY avg_happy DESC)
WHERE happy_rank IN (1,
					ROUND(song_count / 4), 
					ROUND(song_count / 2), 
					ROUND(3 * song_count / 4),
					song_count);'''


Artist_Danceability = '''
CREATE VIEW Artist_Danceability AS
SELECT artist_name, song_name, danceability, dance_rank
FROM
	(SELECT artist_song.artist_name artist_name,
		artist_song.song_name song_name,
		Track_Feature.danceability danceability,
		RANK() OVER (PARTITION BY artist_name ORDER BY 
					Track_Feature.danceability DESC, artist_song.track_id) dance_rank,
		COUNT() OVER (PARTITION BY artist_name) song_count,
		AVG(Track_Feature.danceability) OVER (PARTITION BY artist_name) avg_dance
	FROM
		(SELECT artist_album.artist_name artist_name,
			Track.song_name song_name, 
			Track.track_id track_id
		FROM (SELECT Artist.artist_name, Album.album_id
			FROM Artist JOIN Album 
			ON Artist.artist_id = Album.artist_id) artist_album
		JOIN Track
		ON artist_album.album_id = Track.album_id) artist_song
	JOIN Track_Feature
	ON artist_song.track_id = Track_Feature.track_id
	ORDER BY avg_dance DESC)
WHERE dance_rank IN (1, 
					ROUND(song_count / 4), 
					ROUND(song_count / 2), 
					ROUND(3 * song_count / 4),
					song_count);'''
					
Scatter_Data = '''
CREATE VIEW Scatter_Data AS
SELECT followers, popularity, release_date, danceability, energy, instrumentalness,
		liveness, loudness, speechiness, tempo, valence
FROM
	(SELECT followers, popularity, release_date, track_id FROM
		(SELECT followers, popularity, album_id, release_date 
		FROM
		Artist JOIN Album ON Artist.artist_id = Album.artist_id) Artist_Album
	JOIN Track ON Artist_album.album_id = Track.album_id) Artist_Album_Track
JOIN Track_Feature ON Artist_Album_Track.track_id = Track_Feature.track_id'''
	


views = {'Artists_6_Longest_Songs': Artists_6_Longest_Songs,
'Artists_By_Followers': Artists_By_Followers,
'Artists_6_Fastest_Songs': Artists_6_Fastest_Songs,
'Artist_Happiness': Artist_Happiness,
'Artist_Danceability': Artist_Danceability,
'Scatter_Data': Scatter_Data}

make_views(views)

# SD = pd.read_sql_query('Select * from Scatter_Data;', con=con)
# print(SD.head())
	
# Note - The Artists_6_Fastest_Songs view actually shows the limitations of automated 
# tempo analysis. I did a spot check of the fastest detected songs by each artist, and
# only three of the twenty tempo analyses were correct.
# Below are the fastest songs of each artist according to Spotify data, followed by 
# the actual bpm, measured manually.

# 'The Yardbirds', 'Like Jimmy Reed Again - 2015 Remaster', 216.072 -- 73
# 'Yusuf / Cat Stevens', 'Tea For The Tillerman', 211.315  -- 116
# 'Modest Mouse', "This Devil's Workday", 210.025 -- 104
# 'Snoop Dogg', 'Do You Like I Do (feat. Lil Duval', 209.901) -- 106
# 'Sheryl Crow', "You're An Original", 208.045 -- 104
# 'Gorillaz', 'To Binge (feat. Little Dragon)', 206.473 -- 104
# 'Stray Cats', "You Can't Hurry Love", 205.928 -- 205
# 'Bee Gees', 'How Can You Mend A Broken Heart', 205.772 -- 68
# 'Scorpions', 'Slave Me', 201.833 -- 101
# 'Arctic Monkeys', 'If You Were There, Beware', 201.1 -- 135 (complex drum pattern, midsection with dotted eighth rhythm)
# 'The Boomtown Rats', "She's So Modern", 200.983 - 201
# 'Owl City', 'Early Birdie', 199.863 -- 100
# 'Bad Bunny', 'La Corriente', 196.12 -- 98
# 'Blue Öyster Cult', "Buck's Boogie - Remastered", 188.102 -- 188
# 'Foals', 'Exits', 188.066 -- 94
# 'Three Dog Night', 'One', 185.532 -- 123 (3/2 polyrhythm)
# 'Counting Crows', 'Hanging Tree', 184.165 -- 92
# 'Danger Mouse', 'Perfect Hair', 183.401 -- 92
# 'Phish', "What's the Use - Live", 183.275 -- 49
# 'Buffalo Springfield', 'Hung Upside Down', 177.287 -- 86



