import twitter, timeit, sys
from time import time
from bitly_api import Connection
from operator import itemgetter
from heapq import nlargest
from re import findall
from oauthtwitter import OAuthApi

# OAuth for Twitter API.
def startAPIs(C_KEY, C_SEC, A_TOKEN):
	twtr = OAuthApi(consumer_key=C_KEY, consumer_secret=C_SEC, 
	                access_token=A_TOKEN)
	return twtr

def statusAge(x, page):
	return (time() - page[x].created_at_in_seconds) / (60*60)

def getHighFive(bitly, twtr, user):
	statuses = []
	statusListIsComplete = False
	pagenum = 1
	
	# Start pulling pages of statuses. As long as the last status 
	# on a given page is not older than 24h, keep pulling pages.
	while (not statusListIsComplete):
		x = -1
		page = twtr.GetFriendsTimeline(user=str(user), page=pagenum, count=100)	

		# Skip this while loop altogether if the oldest status is 
		# <24 hours old. Else, kick into binary search until the 
		# search zeroes in on the same index. Instantiated x 
		# above so I could use it as an index here.
		while (statusAge(x, page) > 24.0):
			lastIndex = 0
			newer = -1*len(page)          # more negative = NEWER
			older = -1                    # less negative = OLDER
			if (x != -1):
				if (statusAge(x, page) <= 24.0): newer = (newer + older)/2
				elif (statusAge(x, page) > 24.0): older = (newer + older)/2
			last = x
			x = (newer + older)/2
			if (last == x): 
				statusListIsComplete = True
				break

		if (not statusListIsComplete):
			statuses.append(page)
			pagenum += 1

	# Then append the remaining tweets once we find the last tweet.
	statuses.append(page[:x])

	# List-flattening list comprehension.
	statuses = [item for sublist in statuses for item in sublist]
	print "%i tweets from friends in the last 24 hours." % len(statuses)

	# Instantiating a list for the bit.ly hashes. Then scan every friend's 
	# status for bit.ly links, store those hashes in a dictionary.
	hashes = []
	clicksByHash = {}
	for s in statuses:
		#print s.user.screen_name
		r = findall(r"[a-z]{1,5}\.[a-z]{1,3}/[A-Za-z0-9]{6}", s.text)
		if len(r) > 0:    # if the status has a bit.ly link
			print r[0][:-7]
			if r[0][:-7] != "su.pr" and "t.co" and "ow.ly" and "say.ly":
				h = r[0][-6:]
				try:
					clicksByHash[h] = (bitly.clicks(h)[0]['global_clicks'],
										   s.user.screen_name)
				except KeyError or BitlyError:
					#print s.text
					continue
			else:
				#print "Found a Twitter or StumbleUpon hash!"
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
		if (hi5[h]['title'] == None): hi5[h]['title'] = "No title."
		print "From %s (with %i clicks)" % (hi5[h]['source'], clicksByHash[h][0])
		print "URL: %s\n" % hi5[h]['url']

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
