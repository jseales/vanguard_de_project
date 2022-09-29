#!/usr/bin/python3


import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import pprint
from sqlalchemy import create_engine
from sqlalchemy.types import VARCHAR, INTEGER, BOOLEAN, REAL
import sqlite3

# Ingestion


# For some reason, the spotipy auth_manager couldn't automatically access
# my environment variables. That's why I use the os module to access them. 
# I think it should be all right because I'm still not hard coding the
# credentials. 
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOITPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
scope = 'user-library-read'

auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, 
redirect_uri=redirect_uri, scope=scope)

sp = spotipy.Spotify(auth_manager=auth_manager)


band_names = [
    "Arctic Monkeys",
    "Bad Bunny",
    "Bee Gees",
    "Blue Oyster Cult",
    "Boomtown Rats",
    "Buffalo Springfield",
    "Cat Stevens",
    "Counting Crows",
    "Danger Mouse",
    "Foals",
    "Gorillaz",
    "Modest Mouse",
    "Owl City",
    "Phish",
    "Scorpions",
    "Sheryl Crow",
    "Snoop Dogg",
    "Stray Cats",
    "Three Dog Night",
    "Yardbirds"]

# def make_db(rules_dict, first_only=False):
	



Artist = pd.DataFrame(columns=['artist_name', 
'external_url', 
'genre', 
'image_url', 
'followers', 
'popularity', 
'type', 
'artist_uri'])

for artist in band_names:
	item = sp.search(artist, type='artist')['artists']['items'][0]
	# we only need the first member of 'items' because the rest of them are 
	# different artists that may also come up in a search using the terms from 
	# the list of band_names. 
	
	Artist.loc[item['id']] = pd.Series({'artist_name':item['name'], 
	'external_url':item['external_urls']['spotify'], 
	'genre':item['genres'][0], 
	'image_url':item['images'][0]['url'], 
	'followers':item['followers']['total'], 
	'popularity':item['popularity'], 
	'type':item['type'], 
	'artist_uri':item['uri']})




Album = pd.DataFrame(columns=['album_name', 
'external_url', 
'image_url', 
'release_date', 
'total_tracks',
'type',
'album_uri',
'artist_id'])

for artist_id in Artist.index:
	items = sp.artist_albums(artist_id, album_type='album', country='US')['items']
	for item in items:
		Album.loc[item['id']] = pd.Series({'album_name':item['name'],
		'external_url':item['external_urls']['spotify'],
		'image_url':item['images'][0]['url'],
		'release_date':item['release_date'],
		'total_tracks':item['total_tracks'],
		'type':item['type'],
		'album_uri':item['uri'],
		'artist_id':artist_id})




Track = pd.DataFrame(columns=['song_name',
'external_url',
'duration_ms',
'explicit',
'disc_number',
'type',
'song_uri',
'album_id'])

for album_id in Album.index:
	items = sp.album_tracks(album_id=album_id, limit=50, offset=0)['items']
	for item in items:
		Track.loc[item['id']] = pd.Series({'song_name':item['name'],
		'external_url':item['external_urls']['spotify'],
		'duration_ms':item['duration_ms'],
		'explicit':item['explicit'],
		'disc_number':item['disc_number'],
		'type':item['type'],
		'song_uri':item['uri'],
		'album_id':album_id})

		
		
		
Track_Feature = pd.DataFrame(columns=['danceability',
'energy',
'instrumentalness',
'liveness',
'loudness',
'speechiness',
'tempo',
'type',
'valence',
'song_uri'])

featureless_tracks = []
for track_id in Track.index:
	item = sp.audio_features([track_id])[0]
	if item:
		Track_Feature.loc[track_id] = pd.Series({'danceability':item['danceability'], 
		'energy': item['energy'], 
		'instrumentalness': item['instrumentalness'], 
		'liveness': item['liveness'], 
		'loudness': item['loudness'], 
		'speechiness': item['speechiness'], 
		'tempo': item['tempo'], 
		'type': item['type'], 
		'valence': item['valence'], 
		'song_uri': item['uri']})
	else:
		print('track id ' + track_id + ' has no audio feautres and will be removed from Track and Track_Feature.')
		featureless_tracks.append(track_id)
		



# Transformation

# For some tracks, the call to audio_features returns None.
# Upon examination, each is a spoken intro. They weren't entered into Track_Feature;
# we should remove them from Track as well. 
Track = Track.drop(featureless_tracks)


# I need to fix missing values in the Album table's release_date column.
# Some of them have just the year and month, and some have only the year. 
# I'm going to fill missing values with 01, as per Jeff Rose's suggestion. 
# However it strikes me as risky, because it could lead to a mistaken impression
# that the first of the month, and especially Jan 1, are the most popular 
# release dates. 
year_only_ix = Album[Album['release_date'].str.len() == 4].index
for ix in year_only_ix:
	Album.at[ix, 'release_date'] += '-01-01'

no_day_ix = Album[Album['release_date'].str.len() == 7].index
for ix in no_day_ix:
	Album.at[ix, 'release_date'] += '-01'



# I tried some different ways of finding duplicate albums, and they didn't give
# exactly the same results, which allowed me to explore some interesting edge cases.
# First, I found albums with the same name and same track count.
Album_dup1 = pd.merge(Album, Track, left_index=True, right_on='album_id')
Album_dup1 = Album_dup1.groupby(['album_id'])['song_name'].count()
Album_dup1 = pd.merge(Album_dup1, Album, left_index=True, right_index=True)[['album_name', 'song_name', 'album_uri']]
Album_dup1 = Album_dup1.sort_values('album_name')
Album_dup1 = Album_dup1[Album_dup1.duplicated(subset=['album_name', 'song_name'], keep=False)]
# pprint.pprint(Album_dup1)

# Secondly I found albums that had the same length in milliseconds for each of the
# songs on the album.
Album_Tracks = pd.DataFrame(index=Album.index, columns=range(60))
for album_id in Album.index:
	for i, track_id in enumerate(Track[Track['album_id'] == album_id].index):
		Album_Tracks.loc[album_id][i] = Track.loc[track_id]['duration_ms']
Album_dup2_ix = Album_Tracks[Album_Tracks.duplicated(keep=False)].index
Album_dup2 = Album.loc[Album_dup2_ix]
Album_dup2 = Album_dup2[['album_name', 'album_uri']].sort_values('album_name')
# pprint.pprint(Album_dup2)

# One pair of albums appears on Album_dup2, but not on Album_dup1: Scorpions 'Return 
# to Forever' and 'Return to Forever (Tour Edition)'. Spot checking by looking up the
# song_uri's on Spotify, I am convinced that they are exactly the same despite the 
# different name. Maybe the tour edition had different album artwork, but for our 
# purposes, I will consider them duplicates. 

# Let's also find out which of the albums that are possibly duplicates are
# actually clean / explicit versions, which I'll treat as distinct albums. 
Album_explicit = pd.DataFrame(index=Album_dup1.index.union(Album_dup2.index), columns=range(60))
for album_id in Album.index:
	for i, track_id in enumerate(Track[Track['album_id'] == album_id].index):
		Album_Tracks.loc[album_id][i] = Track.loc[track_id]['explicit']
Album_c_e_ix = Album_explicit[~Album_Tracks.duplicated(keep=False)].index
Album_c_e = Album.loc[Album_c_e_ix]
Album_c_e = Album_c_e[['album_name', 'album_uri']].sort_values('album_name')
# pprint.pprint(Album_c_e)

# Danger Mouse's 'Cheat Codes' and Snoop Dogg's 'I Wanna Thank Me' and 
# 'Snoop Dogg Presents Algorithm' have clean / explicit pairs, which I will
# leave in the database.

# 
# There are four albums on Album_dup1 that are not on Album_dup2.
# Boomtown Rats' 'Citizens of Boomtown (Deluxe)' and Sheryl Crow's 'The Globe Sessions'
# Both have slightly different song lengths for some of the tracks, but appear
# otherwise identical. I will consider them duplicates. 
# Snoop Dogg's 'I Wanna Thank Me' has an explicit and clean versions. I'll consider them
# to be different albums.
# The last song on Gorillaz 'Laika Come Home' in one version is several minutes longer
# because it contains an additional hidden track. I'll consider them to be different 
# albums.
#
# Now, I'll change the 'Return to Forever (Tour Edition)' title to 'Return to Forever'
# to make it easier to remove the duplicate. 
Album_dup2.loc['2maecX2Rg0DCNDohhlndau']['album_name'] = 'Return to Forever'
# And then add Boomtown Rats' 'Citizens of Boomtown (Deluxe)' and Sheryl Crow's 
# 'The Globe Sessions' to Album_dup2.
to_add = Album_dup1[Album_dup1['album_name'].isin(['The Globe Sessions', 'Citizens of Boomtown (Deluxe)'])]
Album_dup = pd.concat([Album_dup2, to_add])
# Then take out the albums that are clean / explicit pairs.
Album_dup = Album_dup[~Album_dup['album_name'].isin(['Cheat Codes', 'I Wanna Thank Me', 'Snoop Dogg Presents Algorithm'])]
# pprint.pprint(Album_dup)

# Finally we have the list of albums that have duplicates we need to remove.

Album_dup_delete = Album_dup[Album_dup.duplicated(subset='album_name', keep='first')]
album_id_delete = Album_dup_delete.index
Album.drop(album_id_delete)

#Let's also drop all the tracks that are on those albums from Track and Track_Feature

track_id_delete = Track[Track['album_id'].isin(album_id_delete)].index
Track = Track.drop(track_id_delete)
Track_Feature = Track_Feature.drop(track_id_delete)


# Now let's drop all other tracks that are redundant. I'll consider them duplicates
# if they have the same name, explicit labeling, duration, and artist.
Album_Track = pd.merge(Track, Album, left_on='album_id', right_index=True)
Album_Track = Album_Track[['song_name','explicit','duration_ms','artist_id']]
track_id_delete = Track[Album_Track.duplicated(keep='first')].index
Track = Track.drop(track_id_delete)
Track_Feature = Track_Feature.drop(track_id_delete)


# There could be problematic NaN values, but calls to table.info() show that there
# are none. I feel lucky!
# pprint.pprint(Artist.info())
# pprint.pprint(Album.info())
# pprint.pprint(Track.info())
# pprint.pprint(Track_Feature.info())

# I'm going to consider the data to be clean now. I hope I didn't miss anything important!

# Now let's save the tables to the spotify.db database. 

Artist_dtypes = {'artist_id': VARCHAR(50),
				'artist_name': VARCHAR(255),
				'external_url': VARCHAR(100),
				'genre': VARCHAR(100),
				'image_url': VARCHAR(100),
				'followers': INTEGER,
				'popularity': INTEGER,
				'type': VARCHAR(50),
				'artist_uri': VARCHAR(100)}
				
Album_dtypes = {'album_id': VARCHAR(50),
				'album_name': VARCHAR(255),
				'external_url': VARCHAR(100),
				'image_url': VARCHAR(100),
				'release_date': VARCHAR(10),
				'total_tracks': INTEGER,
				'type': VARCHAR(50),
				'album_uri': VARCHAR(100),
				'artist_id': VARCHAR(50)}

Track_dtypes = {'track_id': VARCHAR(50),
				'song_name': VARCHAR(255),
				'external_url': VARCHAR(100),
				'duration_ms': INTEGER,
				'explicit': BOOLEAN,
				'disc_number': INTEGER,
				'type': VARCHAR(50),
				'song_uri': VARCHAR(100),
				'album_id': VARCHAR(50)}

Track_Feature_dtypes = {'track_id': VARCHAR(50),
				'danceability': REAL(precision=2),
				'energy': REAL(precision=2),
				'instrumentalness': REAL(precision=2),
				'liveness': REAL(precision=2),
				'loudness': REAL(precision=2),
				'speechiness': REAL(precision=2),
				'tempo': REAL(precision=2),
				'type': VARCHAR(50),
				'valence': REAL(precision=2),
				'song_uri': VARCHAR(100)}

				
engine = create_engine('sqlite:///spotify.db')

Artist.to_sql('Artist', con=engine, if_exists='replace', 
			index_label='artist_id', dtype=Artist_dtypes)
Album.to_sql('Album', con=engine, if_exists='replace', 
			index_label='album_id', dtype=Album_dtypes)
Track.to_sql('Track', con=engine, if_exists='replace', 
			index_label='track_id', dtype=Track_dtypes)
Track_Feature.to_sql('Track_Feature', con=engine, if_exists='replace', 
			index_label='track_id', dtype=Track_Feature_dtypes)



con = sqlite3.connect('spotify.db')
cur = con.cursor()
a = cur.execute('Select * from sqlite_schema')
for row in a:
	pprint.pprint(row)

