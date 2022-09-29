# Lauren Seales Vanguard / Onramp Data Engineering Project

## Contents
	*ingest_transform.py
	*views.py
	*visualize.py
	*spotify.db
	*visualizations.pdf

### ingest_transform.py
First I create an instance of spotipy.Spotify which will gather data.
I define my list of bands, who represent a variety of styles and time periods. 
They all have animal-themed band names. 
I ingest data via the spotipy API, and store it in four DataFrames:
* Artist
* Album
* Track
* Track_Feature

Then I begin the process of cleaning data. 
First I delete some rows from Track that correspond with audio tracks for which no audio
features were provided by Spotify. I checked them, and found that each was a spoken intro,
and thus not important to this project.
Then I grapple with the somewhat complex issue of what constitutes a duplicate album. I
approach the issue a few different ways, and finally settle on criteria for what albums are 
redundant and should be removed. My comments in this section are pretty verbose. They 
detail my thinking and the decisions I made. 
I remove tracks from Track and Track_Feature that were on the removed albums.
Then I remove further duplicate tracks that were not on duplicate albums.
I check for NaNs and find none. 
Finally I create a SQLite database 'spotify.db' and save the data from each DataFrame as 
a table in it. The tables have the same names as the DataFrames:

* Artist
* Album
* Track
* Track_Feature

### views.py
I define a convenience function make_views that will execute SQL code. Then 
I store the necessary CREATE VIEW statements as strings to variables which are then passed
to the make_views function. 
Views created:
* Artists_6_Longest_Songs
* Artists_By_Followers
* Artists_6_Fastest_Songs
* Artist_Happiness
* Artist_Danceability
* Scatter_Data

**Artists_6_Longest_Songs**
Finds the 6 longest songs for each artist. They are ordered by descending length, 
with each artist's 6 tracks on consecutive rows. The artists are ordered by their average
song length. 

**Artists_By_Followers**
Represents the number of followers for each artist, ordered in descending order of follower
quantity. 

**Artists_6_Fastest_Songs**
Finds the 6 fastest songs for each artist, as reported by Spotify data. They are ordered
in descending tempo, with each artist's 6 tracks on consecutive rows. The artists are ordered
by their average tempo.

**Artist_Happiness**
Looks at the distribution of valence for each artist's discography. 'Happiness' is an imperfect
synonym for valence, but it evokes nearly the right idea. For each artist, 5 data points are
recorded, corresponding to the maximum, 75th percentile, 50th percentile, 25th percentile, 
and minimum values for valence for songs in their catalogue. The 5 data points are stored
consecutively, and the artists are ordered by average valence.

**Artist_Danceability**
Looks at the distribution of danceability for each artist's discography For each artist, 
5 data points are recorded, corresponding to the maximum, 75th percentile, 50th percentile, 
25th percentile, and minimum values for danceability for songs in their catalogue. The 5 
data points are stored consecutively, and the artists are ordered by average danceability.

**Scatter_Data**
Gathers together the popularity and follower count of its artist, the release date, and 
track feature values for each track in the database. These are used in various combinations
to create scatter plots in visualize.py

I end the file with a long comment about the unreliability of tempo data from Spotify, 
which I uncover by comparing actual tempo values of the songs to their reported values.

### visualize.py
I open a connection to the spotify database.
I retrieve data from the views created in views.py and store them in DataFrames.
I define a function recolumn that is useful for reshaping the DataFrames so that 
they are suitable for the bar graphs I create. 
I define a function make_bar_graph that takes data, sizing, and labeling information and 
then creates and saves an image of a bar graph.
Then I perform the recolumn-ing, and make bar graphs by calls to make_bar_graph.
I define a function make_scatter_plot that takes data, sizing, labeling, and coloring 
information, and then creates and saves an image of a scatter plot.
I perform some data transformation to make the 'release_date' and 'followers' columns more
useful for the scatter plots.
Finally I make scatter plots by calls to make_scatter_plots.

### spotify.db
An SQLite database containing the tables and views described above.

### visualizations.pdf
Eight visualizations are contained: four scatter plots and four bar graphs. If evaluators 
wish only three, please choose the first three pages in the document.

