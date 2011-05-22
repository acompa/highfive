import twitter, timeit, sys
from time import time
from datetime import datetime, timedelta
from calendar import timegm
from bitly_api import Connection
from operator import itemgetter
from heapq import nlargest
from re import findall
from oauthtwitter import OAuthApi

# Testing program performance
from timeit import timeit, Timer
from random import randint

def startAPIs(C_KEY, C_SEC, A_TOKEN):
	twtr = OAuthApi(consumer_key=C_KEY, consumer_secret=C_SEC, access_token=A_TOKEN)
	return twtr

def status_age(tweet):
	return (datetime.now() - tweet.created_at)

def get_highfive(bitly, twtr, user):
	statuses = []
	completedList = False
	pagenum = 0
	dt = timedelta(seconds = 86401)
	
	# Start pulling pages of statuses. As long as the last status 
	# on a given page is not older than 24h, keep pulling pages.
	while not completedList:
		if pagenum != 0:
			statuses.append(page)
		pagenum += 1
		page = twtr.friends_timeline(user=user, page=pagenum, count=200)	
		pagelen = len(page)
		print pagelen
		x = pagelen - 1
		
		# Have we exceeded the # of allowed API calls?
		if pagelen == 0: 
			break
		
 		# Use binary search to find the last update from 24hrs ago.
		if status_age(page[x]) > dt:
			if status_age(page[0]) > dt:
				x = 0
				break
			newest = 0          
			oldest = pagelen - 1
			x = (newest + oldest) / 2
			while True:
				x = (newest + oldest) / 2
				if x != pagelen:
					if status_age(page[x]) <= dt:
						newest = x 
					if status_age(page[x]) > dt:
						oldest = x

				if status_age(page[x]) > dt and status_age(page[x - 1]) <= dt \
				or status_age(page[x]) <= dt and status_age(page[x + 1]) > dt:
					completedList = True
					break

	statuses.append(page[:x])

	# List-flattening list comprehension.
	statuses = [item for sublist in statuses for item in sublist]
	print "%i tweets from friends in the last 24 hours." % len(statuses)
	print "Oldest tweet at", statuses[-1].created_at

	# Instantiating a list for the bit.ly hashes. Then scan every friend's 
	# status for bit.ly links, store those hashes in a dictionary.
	hashes = []
	clicksByHash = {}
	for s in statuses:
		r = findall(r"[a-z]{1,5}\.[a-z]{1,3}/[A-Za-z0-9]{6}", s.text)
		if len(r) > 0:
			if r[0][:-7] != "su.pr" and "t.co" and "ow.ly" and "say.ly":
				h = r[0][-6:]
				try:
					clicksByHash[h] = (bitly.clicks(h)[0]['global_clicks'],
									   s.user.screen_name)
				except KeyError or BitlyError:
					#print s.text
					continue
		else:
			continue
		hashes.append(h)
		
	# Now take the bit.ly dictionary, sort based on total clicks.
	topHashes = [h[0] for h in nlargest(5, clicksByHash.iteritems(), itemgetter(1))]
	print topHashes

	hi5 = {}
	for h in topHashes:
		hi5[h] = {'title' : bitly.info(h)[0]['title'], 
	          	  'url'   : bitly.expand(h)[0]['long_url'],
	          	  'clicks': clicksByHash[h][0],
	              'cpm'   : sum(bitly.clicks_by_minute(h)[0]['clicks']),
	              'cpd'   : bitly.clicks_by_day(h)[0]['clicks'][0]['clicks'],
	              'source': clicksByHash[h][1],
			      'score' : 0}
		if (hi5[h]['title'] == None): 
			try:
				from urllib import urlopen
				from BeautifulSoup import BeautifulSoup
				soup = BeautifulSoup(urlopen(hi5[h]['url']))
				hi5[h]['title'] = soup.title.string
			except:
				hi5[h]['title'] = "No title."
		# print "From %s (with %i clicks)" % (hi5[h]['source'], clicksByHash[h][0])
		# print "URL: %s\n" % hi5[h]['url']

	# Storing top five data to a MySQL db.

	from django.db import models
	from models import Hashdata

	for h in topHashes:
		x = Hashdata(username = user,
                     bhash = h, 
					 title = hi5[h]['title'], 
					 url = hi5[h]['url'], 
					 time = time(), 
					 clicks = hi5[h]['clicks'], 
					 cpm = hi5[h]['cpm'],
					 cpd = hi5[h]['cpd'],
					 source = hi5[h]['source'],
					 score = hi5[h]['score'])
		x.save()
		
# Voting functionality.
# if user clicks on vote button:
# 	x = Hashdata.objects.get(hash='xxxxxx')
# 	x.vote = 1
# 	x.save()
