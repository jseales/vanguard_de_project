#!/usr/bin/python3


import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
import sqlite3
import pprint



con = sqlite3.connect('spotify.db')


Artists_6_Longest_Songs = pd.read_sql_query('Select * from Artists_6_Longest_Songs;', con=con)
Artists_By_Followers = pd.read_sql_query('Select * from Artists_By_Followers;', con=con)
Artists_6_Fastest_Songs = pd.read_sql_query('Select * from Artists_6_Fastest_Songs;', con=con)
Artist_Happiness = pd.read_sql_query('Select * from Artist_Happiness;', con=con)
Artist_Danceability = pd.read_sql_query('Select * from Artist_Danceability;', con=con)
Scatter_Data = pd.read_sql_query('Select * from Scatter_Data;', con=con)



def recolumn(df, indexmod, datacol, colnames):
	'''reshapes the data so that it's ready for pyplot.
	df: pd DataFrame. The input DataFrame.
	indexmod: Int. How many of the input index values to stride to generate the output index.
	datacol: String. The column of the input DataFrame containing the relevant data.
	colnames: List of Strings. The column names for the new DataFrame. They will become the legend labels.
	function output: pd DataFrame. A new DataFrame that is ready for pyplot.'''
	result = pd.DataFrame(index=df['artist_name'][::indexmod], columns=colnames)
	for m in range(20):
		for n in range(indexmod):
			result.at[result.index[m], result.columns[n]] = df[datacol][indexmod * m + n]
	return result
	
def make_bar_graph(df, figsize, title, xlabel, ylabel, png_name, yticksfreq, ymax):
	'''Makes and saves a png of an unstacked bar graph.
	df: pd DataFrame. A recolumnized DataFrame ready for pyplot.
	figsize: (int, int) The size of the plot.
	title: String. The title text for the plot.
	xlabel: String. Text for the x axis label.
	ylabel: String. Text for the y axis label. 
	png_name: The name of the png file to be saved.
	yticks_freq: Float. The frequency of y axis tick labels.'''
	plt.clf()
	df.plot(kind='bar', figsize=figsize, fontsize=20, cmap='winter_r')
	plt.title(title, fontsize=30)
	plt.xlabel(xlabel, fontsize=24)
	plt.xticks(rotation=30, horizontalalignment='right')
	plt.ylabel(ylabel, fontsize=24)
	plt.yticks(np.arange(0, ymax, yticksfreq))
	plt.legend(bbox_to_anchor=(1.05,1), loc='upper right', borderaxespad=0, fontsize=16)
	plt.subplots_adjust(bottom=0.25)
	plt.savefig(png_name+'.png')


A_6_L_S = recolumn(Artists_6_Longest_Songs, 6, 'song_length', ['1st', '2nd', '3rd', '4th', '5th', '6th'])
A_6_F_S = recolumn(Artists_6_Fastest_Songs, 6, 'tempo', ['1st', '2nd', '3rd', '4th', '5th', '6th'])
A_H = recolumn(Artist_Happiness, 5, 'happiness', ['max','75%','50%','25%','min'])
A_D = recolumn(Artist_Danceability, 5, 'danceability', ['max','75%','50%','25%','min'])


make_bar_graph(A_6_L_S, (30,25), "The Six Longest Songs in Artists' Discography",\
"Average Song Length, Decreasing", "Song Length (Minutes)", "Artists_6_Longest_Songs", 2, 75)
make_bar_graph(A_6_F_S, (30, 10), "The Six Fastest Songs in Artists' Discography, As (Often Incorrectly) Measured by Spotify", \
"Average Tempo, Decreasing", "Tempo, BPM", "Artists_6_Fastest_Songs", 20, 240)
make_bar_graph(A_H, (30,10), "Happiness (Valence) of Artists' Discography", \
"Average Happiness, Decreasing", "Happiness (Valence)", "Artist_Happiness", 0.2, 1)
make_bar_graph(A_D, (30, 10), "Danceability of Artists' Discography",\
"Average Danceability, Decreasing", "Danceability", "Aritst_Danceability", 0.2, 1)



def make_scatter_plot(df, x, xticks, y, figsize, title, xlabel, ylabel, png_name, cmap):
	'''Makes scatter plots from specified columns in a DataFrame.
	df: pd.DataFrame. The DataFrame containing data for the plot
	x: String. The column name for the x axis data
	xticks: Array-like. The locations for ticks on the x axis.
	y: String. The column name for the y axis data.
	figsize: (float, float). The size of the plot.
	title: String. The title to be printed above the plot.
	xlabel: String. The label for the x axis.
	ylabel: String. The label for the y axis.
	png_name: String. The filename for the saved graph.
	cmap: String. The color map to use for the plot.'''
	df = df.sort_values(x)
	plt.clf()
	df.plot.scatter(x,y,figsize=(20,10), c=df['popularity'], cmap=cmap, alpha=0.3, s=df['followers'])
	plt.title(title)
	plt.suptitle('color: popularity\nsize: followers')
	plt.subplots_adjust(bottom=0.2)
	plt.xticks(xticks)
	plt.xlabel(xlabel)
	plt.ylabel(ylabel)
	plt.savefig(png_name)
	

Scatter_Data['release_date'] = pd.to_datetime(Scatter_Data['release_date'])
Scatter_Data['followers'] = Scatter_Data['followers'] / 60000.


make_scatter_plot(Scatter_Data, 'release_date', pd.date_range('1966', '2026', periods=7), 'loudness', (20,10), 'Loudness Over Time', \
'Release Date', 'Loudness', 'date_loudness', 'cividis')
make_scatter_plot(Scatter_Data, 'valence', np.linspace(0, 1, 6), 'danceability', (10,10),'Valence and Danceability', \
'Valence', 'Danceability', 'valence_danceability', 'cool')
make_scatter_plot(Scatter_Data, 'loudness', np.linspace(-30, 0, 6), 'energy', (10,10),'Loudness and Energy', \
'Loudness', 'Energy', 'loudness_energy', 'magma')
make_scatter_plot(Scatter_Data, 'loudness', np.linspace(-30, 0, 6), 'instrumentalness', (10,10),'Loudness and Instrumentalness', \
'Loudness', 'Instrumentalness', 'loudness_instrumentalness', 'magma')
