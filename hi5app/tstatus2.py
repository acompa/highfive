import sys
from time import time
from datetime import datetime, timedelta
from calendar import timegm
from re import findall

# Testing program performance
#from timeit import timeit, Timer
#from random import randint

def status_age(tweet):
	return (datetime.now() - tweet.created_at)

def scrape_timeline(bitly, twtr, user):
	"""
	Will return a list of global bit.ly hashes, sorted by the # of clicks
	on each. Will also save sorted list to SQL table.
	
	NOTE: replace clicks with recommendation score in a future revision.
	"""
	statuses = []
	completedList = False
	pagenum = 0
	oneDay = timedelta(seconds = 86401)
	
	# Start pulling pages of statuses. As long as the last status 
	# on a given page is not older than 24h, keep pulling pages.
	while not completedList:
		if pagenum != 0:
			statuses.append(page)
		pagenum += 1
		page = twtr.friends_timeline(user=user, page=pagenum, count=200)	
		pagelen = len(page)
		x = pagelen - 1
		
		# Have we exceeded the # of allowed API calls?
		if pagelen == 0: 
			break
		
 		# Use binary search to find the last update from 24hrs ago.
		if status_age(page[x]) > oneDay:
			if status_age(page[0]) > oneDay:
				x = 0
				break
			newest = 0          
			oldest = pagelen - 1
			x = (newest + oldest) / 2
			while True:
				x = (newest + oldest) / 2
				if x != pagelen:
					if status_age(page[x]) <= oneDay:
						newest = x 
					if status_age(page[x]) > oneDay:
						oldest = x

				if status_age(page[x]) > oneDay and status_age(page[x - 1]) <= oneDay \
				or status_age(page[x]) <= oneDay and status_age(page[x + 1]) > oneDay:
					completedList = True
					break

	statuses.append(page[:x])

	# List-flattening list comprehension.
	statuses = [item for sublist in statuses for item in sublist]
	print "%i tweets from friends in the last 24 hours." % len(statuses)
	print "Oldest tweet at", statuses[-1].created_at

	# Instantiating a list for the bit.ly hashes. Then scan every friend's 
	# status for bit.ly links, store those hashes in a dictionary.
	timelineData = {}
	for s in statuses:
		r = findall(r"[a-z]{1,5}\.[a-z]{1,3}/[A-Za-z0-9]{6}", s.text)
		if len(r) > 0:
			if r[0][:-7] != "su.pr" and "t.co" and "ow.ly" and "say.ly":
				h = r[0][-6:]
				try:
					globalHash = bitly.clicks(h)[0]['global_hash']
					# Saving # of times the hash appears in user's timeline.
					if globalHash in timelineData:
						timelineData[globalHash]['timeline_count'] += 1
					else:
						timelineData[globalHash] = {'source': s.user.screen_name,
						                            'timeline_count': 0,
						                            'clicks': bitly.clicks(globalHash)[0]['global_clicks']}
				except KeyError or BitlyError:
					#print s.text
					continue
		else:
			continue
	return timelineData

# def retrieve_clicks_per_hash(bitly, hashes):
# 	"""
# 	Returns a hash-click dictionary.
# 	"""
# 	clicksPerHash = {}
# 	for h in hashes:
# 		clicksPerHash[h] = bitly.clicks(h)[0]['global_clicks']		
# 	return clicksPerHash

def get_bitly_info(bitly, incompleteHashData):
	"""
	Queries the bit.ly API for information on each hash, then
	returns the results. Also updates the bit.ly SQL table.
	"""
	
	completeHashData = {}
	
	for row in incompleteHashData:
		h = row.bhash			
		print h
		title = bitly.info(h)[0]['title'] 
		url = bitly.expand(h)[0]['long_url']
		
		row.clicks = bitly.clicks(h)[0]['global_clicks']
		row.cpm = sum(bitly.clicks_by_minute(h)[0]['clicks'])
		row.cpd = bitly.clicks_by_day(h)[0]['clicks'][0]['clicks']
					
		if (title == None): 
			try:
				from urllib import urlopen
				from BeautifulSoup import BeautifulSoup
				soup = BeautifulSoup(urlopen(hi5[h]['url']))
				title = soup.title.string
			except:
				title = "No title."
	
		# Update bit.ly table with titles and URLs for each hash.
		# Can I do this in a batch?
		from models import BitlyHashInfo
		y = BitlyHashInfo(bhash = h,
		                  title = title,
		                  url = url)
		y.save()
		
		completeHashData[h] = {'title': title,
		                       'url': url,
		                       'source': row.source,
		                       'clicks': row.clicks,
							   'score': row.score}
		print completeHashData
		row.save()
		
	return completeHashData

def store_incomplete_hash_info(user, rawTimelineData, t):
	"""
	Save data on bit.ly hashes to MySQL db.
	"""
	from django.db import models
	from models import ModelInputs


	# Do any hashes exist in the SQL db? If so, update the db instead of adding 
	# a new row. Consider moving this logic to tstatus2.py (to avoid looping 
	# over rawTimelineData multiple times).
	if t != None:
		for h in rawTimelineData.keys():
			try:
				query = ModelInputs.objects.get(username = user, bhash = h)
				query.clicks = rawTimelineData[h]['clicks']
				query.source = rawTimelineData[h]['source']
				query.time = t
				query.save()
			except ModelInputs.DoesNotExist:
				x = ModelInputs(username = user,
						bhash = h,
						time = t,
						clicks = rawTimelineData[h]['clicks'],
						cpm = 0,
						cpd = 0,
						timeline_count = rawTimelineData[h]['timeline_count'],
						source = rawTimelineData[h]['source'],
						score = 0)
				x.save()
				
def store_hash_info(user, incompleteHashInfo, t):
	"""
	Save data on bit.ly hashes to MySQL db.
	"""
	from django.db import models
	from models import ModelInputs
	
	if t != None:
		for h in bitlyHashInfo.keys():
			x = ModelInputs(username = user,
			                bhash = h,
			                time = t,
			                clicks = bitlyHashInfo[h]['clicks'],
			                cpm = bitlyHashInfo[h]['cpm'],
			                cpd = bitlyHashInfo[h]['cpd'],
			                timeline_count = bitlyHashInfo[h]['timeline_count'],
			                source = bitlyHashInfo[h]['source'],
			                score = bitlyHashInfo[h]['score'])
			x.save()

def store_timeline_data(user, rawTimelineData, t):
	"""
	Save raw timeline data to MySQL db.
	"""
	from django.db import models
	from models import TimelineData
	
	if t != None:
		for h in rawTimelineData.keys():
			x = TimelineData(username = user,
			                 bhash = h,
			                 time = t,
			                 timeline_count = bitlyHashInfo[h]['timeline_count'],
			                 source = bitlyHashInfo[h]['source'])
			x.save()

def store_new_hash_info(hashList, t):
	"""
	Commands to update MySQL tables with ALL data. Break 
	these commands into their own functions soon.
	"""
	from django.db import models
	from models import HashData, BitlyHashInfo, ModelData
		
	for h in hashList:
		z = ModelInputs(username = user,
		                bhash = h,
		                time = t,
		                clicks = hi5[h]['clicks'], 
		                cpm = hi5[h]['cpm'],
		                cpd = hi5[h]['cpd'],
		                timeline_count = hi5[h]['timeline_count'],
		                source = hi5[h]['source'],
		                score = hi5[h]['score'])
		z.save()
