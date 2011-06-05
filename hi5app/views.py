from django.db import models
from models import ModelInputs
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
#from django.template import Context
#from django.template.loader import get_template
from django.utils import simplejson
from django.contrib.auth import login, authenticate
from django.conf import settings
from django.core.urlresolvers import reverse
#from django.core.context_processors import csrf

from tstatus2 import scrape_timeline, get_bitly_info, store_incomplete_hash_info, store_timeline_data
from bitly_api import Connection
from time import time
from operator import itemgetter
from string import find

#from oauthtwitter import OAuthApi
import tweepy
import oauth.oauth as oauth
 
CONSUMER_KEY = getattr(settings, 'CONSUMER_KEY', None)
CONSUMER_SECRET = getattr(settings, 'CONSUMER_SECRET', None)
 
def twitter_signin(request):
	""" 
	Redirect user to Twitter OAuth login page. 
	"""
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	try:
		signin_url = auth.get_authorization_url()
	except tweepy.TweepError:
		print "Could not get request token!"
	request.session['requestTokenKey'] = auth.request_token.key
	request.session['requestTokenSecret'] = auth.request_token.secret
	return HttpResponseRedirect(signin_url)

def twitter_landing(request):
	""" 
	Landing page for quick Twitter redirects. Captures auth information
	from Twitter's redirect, stores in session, redirects user to 
	empty template.
	"""
	request.session['verifier'] = request.GET.get('oauth_verifier')
	return render_to_response('land.html')

def confirm_OAuth(request):
	""" 
	Pull the OAuth verifier from the user's session and authenticate.
	On success, redirects user to her links page.
	"""
	
	verifier = request.session.get('verifier')
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	
	# Swapping request token for access token, storing access token
	# info in session.
	rTokenKey = request.session.get('requestTokenKey', None)
	rTokenSecret = request.session.get('requestTokenSecret', None)
	auth.set_request_token(rTokenKey, rTokenSecret)
	try:
		auth.get_access_token(verifier)
		qq = auth.access_token
	except tweepy.TweepError:
		print "Error! Failed to get access token!"

	request.session['aKey'] = auth.access_token.key
	request.session['aSecret'] = auth.access_token.secret

	return HttpResponseRedirect(reverse('links'))

def show_link_feed(request):
	""" 
	Home page view. Will perform the following via JS (jQuery):
	1. Authenticate the user and update the page title and user info.
	2. Update hash info for user in SQL db.
	"""
		
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	try:
		auth.set_access_token(request.session.get('aKey'), request.session.get('aSecret'))
	except tweepy.TweepError:
		print "Could not retrieve access token information!"

	# Update user name and picture, store user name in session.
	t_api = tweepy.API(auth)
	user = t_api.verify_credentials().screen_name
	pic = t_api.verify_credentials().profile_image_url
	request.session['user'] = user
	
	return render_to_response('palm.html', {'user':user, 'pic':pic})

def get_hash_data(request):
	""" 
	Obtains data from the user in the following order:
	1. Scrapes user's timeline for any shortened links.
	2. Stores that incomplete info to ModelInputs table.
	3. Redirects user to first page of links.
	"""
	
	# if request.is_ajax():
		
	b_api = Connection('acompa', 'R_9c2643b4c8c85a250493e90ce27a624d')
		
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(request.session.get('aKey', None), 
			      request.session.get('aSecret', None))
	t_api = tweepy.API(auth)
	
	# Scrape user's timeline for hashes, referrers, and # of hash appearances. 
	# Sort the hashes based on # of clicks.
	t = time()
	request.session['t'] = t
	user = request.session.get('user', None)
	rawTimelineData = scrape_timeline(b_api, t_api, user)				
	store_incomplete_hash_info(user, rawTimelineData, t)
	return HttpResponseRedirect('../l/1')

def next_10_links(request, pageNum):
	""" 
	Shows user top 10 links from today (if $PAGENUM == 1) or $PAGENUM - 1 days ago.

	Performs the following:
	1. Filters SQL db for hashes posted $PAGENUM - 1 days ago (or today).
	2. Obtains hash info (title, url, clicks, &c) from bit.ly's API.
	3. Sorts results based on model output (clicks, as of 6/1/11).
	4. Sends sorted list of links to view.
	"""
	
	# if request.is_ajax():
	b_api = Connection('acompa', 'R_9c2643b4c8c85a250493e90ce27a624d')	
	
	# Query the SQL db for a page of hashes. If we're out of hashes for the user, 
	# hide the link for the next page of hashes.
	t = request.session.get('t', None)
	page = int(pageNum)
	n = (page - 1) * 10
	user = request.session.get('user', None)
	if page > 1:
		tMax = t - 86000 * page
		tMin = t - 86000 * (page + 1)
	else:
		tMax = t
		tMin = t - 86000
	try:
		incompleteHashData = query_database(user, tMin, tMax, n1 = n, n2 = n + 10)
		moreLinks = True
	except IndexError:
		incompleteHashData = query_database(user, tMin, tMax, n1 = n)
		moreLinks = False
	
	# If the query is empty, pull more links from today:
	if len(incompleteHashData) == 0:
		moreLinks = False
		try:
			incompleteHashData = query_database(user, t - 86000, t, n1 = n, n2 = n + 10)
		except:
			incompleteHashData = query_database(user, t - 86000, t, n1 = n)
	
	# Query bit.ly API to obtain basic link information, then update ModelInputs 
	# with link info.
	completeHashData = get_bitly_info(b_api, incompleteHashData)
	clicksPerHash = {}
	for h in completeHashData:
		clicksPerHash[h] = completeHashData[h]['clicks']
	
	results = []
	for h in sorted(clicksPerHash.iteritems(), key=itemgetter(1), reverse=True):
		dict = completeHashData[h[0]]
		i = find(dict['url'], '/', 7)
		results.append({'title': dict['title'],
	                	'url': dict['url'][7:i],
	                	'longurl': dict['url'],	
	                	'source': dict['source'],
	                	'bhash': h[0],
						'score': dict['score']})
	return render_to_response('palm2.html', {'results':results, 'moreLinks': moreLinks, 
						      'next': str(page + 1)})
	
def query_database(user, tMin, tMax, n1, n2 = None):
	"""
	Queries SQL db and pulls a block of 10 hashes.
	"""
	
	if n2 != None:
		incompleteHashData = ModelInputs.objects.filter(username=user
	                                           ).filter(time__gte=tMin
	                                           ).filter(time__lte=tMax
	                                           ).order_by("-time", "-clicks")[n1 : n2]
	else:
		incompleteHashData = ModelInputs.objects.filter(username=user
	                                           ).filter(time__gte=tMin
	                                           ).filter(time__lte=tMax
	                                           ).order_by("-time", "-clicks")[n1 : ]
		
	return incompleteHashData

def vote_article(request):
	""" 
	Voting functionality. Retrieves GET request from view with the hash name,
	then increments the hash's score in ModelInputs.

	Returns a JSON dump to view with info on whether vote succeeded.
	"""
	results = {'success':False}
	if request.method == u'GET':
		GET = request.GET
		if GET.has_key(u'bhash') and GET.has_key(u'score'):
			bhash = str(GET[u'bhash'])
			vote = GET[u'score']
			score = ModelInputs.objects.filter(bhash=bhash).order_by("time")[0]
			if vote == u'up':
				score.vote_for_hash()
			if vote == u'down':
				score.down()
			results = {'success':True}
	json = simplejson.dumps(results)
	return HttpResponse(json, mimetype='application/json')

def hello(request):
	""" Test function. """
	return HttpResponse(u"Hello, world!")
	
def print_intro(request):
	return render_to_response('intro.html')
	
def print_about(request):
	return render_to_response('about.html')

def print_terms(request):
	return render_to_response('terms.html')

def print_help(request):
	return render_to_response('help.html')	
