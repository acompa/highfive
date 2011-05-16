from django.db import models
from models import Hashdata
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import Context
from django.template.loader import get_template
from django.utils import simplejson
from django.contrib.auth import login, authenticate
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.context_processors import csrf
from tstatus2 import getHighFive, startAPIs
from bitly_api import Connection
from inspect import getmembers
from time import sleep

from oauthtwitter import OAuthApi
import oauth.oauth as oauth
 
CONSUMER_KEY = getattr(settings, 'CONSUMER_KEY', 'YOUR_KEY')
CONSUMER_SECRET = getattr(settings, 'CONSUMER_SECRET', 'YOUR_SECRET')
 
def twitter_signin(request):
	twitter = OAuthApi(CONSUMER_KEY, CONSUMER_SECRET)
	request_token = twitter.getRequestToken()
	request.session['request_token'] = request_token.to_string()
	signin_url = twitter.getAuthorizationURL(request_token)
	return HttpResponseRedirect(signin_url)
 
def twitter_return(request):
	request_token = request.session.get('request_token', None)
 
	# If there is no request_token for session,
	#    means we didn't redirect user to twitter
	if not request_token:
		# Redirect the user to the login page,
		# So the user can click on the sign-in with twitter button
		return HttpResponse("We didn't redirect you to twitter...")
 
	token = oauth.OAuthToken.from_string(request_token)
 
	# If the token from session and token from twitter does not match
	#   means something bad happened to tokens
	if token.key != request.GET.get('oauth_token', 'no-token'):
		del request.session['request_token']
		# Redirect the user to the login page
		return HttpResponse("Something wrong! Tokens do not match...")
 
	twitter = OAuthApi(CONSUMER_KEY, CONSUMER_SECRET, token)
	access_token = twitter.getAccessToken()
	
	# Save user info.
	t = startAPIs(CONSUMER_KEY, CONSUMER_SECRET, access_token)
	request.session['user'] = t.VerifyCredentials().screen_name
	request.session['pic'] = t.VerifyCredentials().profile_image_url
 
	# print getmembers(access_token)
	auth_user = authenticate(access_token=access_token)
 
	# if user is authenticated then login user
	if auth_user:
		login(request, auth_user)
		request.session['access_token'] = access_token.to_string()
	else:
		# We were not able to authenticate user
		# Redirect to login page
		return HttpResponse("Unable to authenticate you!")
 
	# authentication was successful, user is now logged in
	return HttpResponseRedirect(reverse('links'))

def printHashInfo(request):
	""" Pull top five links from the SQL database, and send them to
	the link view. """
	user = request.session.get('user', None)
	pic = request.session.get('pic', None)
	# t = get_template('palm2.html')
	# html = t.render(Context({'results':results}))
	return render_to_response('palm.html')
		
def getUserInfo(request):
	""" Get user name and picture. """
	if request.is_ajax():
		
		# a = request.session.get('access_token', None)
		# if not a:
		# 	raise
		# a_token = oauth.OAuthToken.from_string(a)
		# t = startAPIs(CONSUMER_KEY, CONSUMER_SECRET, a_token)
		# request.session['user'] = t.VerifyCredentials().screen_name
		# request.session['pic'] = t.VerifyCredentials().profile_image_url
		user = 	request.session.get('user', None)
		pic = request.session.get('pic', None)
		if not user or not pic:
			raise
	
		return render_to_response('info.html', {'user':user, 'pic':pic})
	#return render_to_response('redirect.html')

def getHashInfo(request):
	""" Sorts the data in reverse chronological order, by highest
	number of clicks. General Django rule: perform all business logic
	in views.py and not the HTML. """
	
	if request.is_ajax():
	
		# In the future, ALWAYS use session's 'get' method to retrieve 
		# values.
		a = request.session.get('access_token', None)
		a_token = oauth.OAuthToken.from_string(a)
	
		# Initialize APIs, and get the user's name (redundancy).
		b = Connection('acompa', 'R_9c2643b4c8c85a250493e90ce27a624d')
		t = startAPIs(CONSUMER_KEY, CONSUMER_SECRET, a_token)

		# Calculate the top links and store them to SQL db. Catch
		# any errors in pulling the user's info and redirect them
		# to the login page.
		user = request.session.get('user', None)
		# try:
		# 	getHighFive(b, t, user)
		# except:
		# 	return HttpResponse(u"Could not retrieve your data! Please try again later.")
		getHighFive(b, t, user)
		highFive = Hashdata.objects.filter(username=user).order_by("-time", "clicks")[0:5]
		results = []
		for x in highFive:
			results.append({'title': x.title,
		                	'url': x.url,
		                	'source': x.source,
		                	'bhash': x.bhash})
		return render_to_response('palm2.html', {'results':results})

def hello(request):
	""" Test function. """
	return HttpResponse(u"Hello, world!")
	
def printIntro(request):
	# t = get_template('intro.html')
	# html = t.render(Context())
	return render_to_response('intro.html')
	
def printAbout(request):
	return render_to_response('about.html')

def printTerms(request):
	return render_to_response('terms.html')

def printHelp(request):
	return render_to_response('help.html')	
	
def voteArticle(request):
	""" Setting up voting functionality. """
	results = {'success':False}
	if request.method == u'GET':
		GET = request.GET
		if GET.has_key(u'bhash') and GET.has_key(u'score'):
			bhash = str(GET[u'bhash'])
			vote = GET[u'score']
			score = Hashdata.objects.filter(bhash=bhash).order_by("time")[0]
			if vote == u'up':
				score.up()
			if vote == u'down':
				score.down()
			results = {'success':True}
	json = simplejson.dumps(results)
	return HttpResponse(json, mimetype='application/json')