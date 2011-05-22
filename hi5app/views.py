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
from tstatus2 import get_highfive
from bitly_api import Connection
from inspect import getmembers
from time import sleep

#from oauthtwitter import OAuthApi
import tweepy
import oauth.oauth as oauth
 
CONSUMER_KEY = getattr(settings, 'CONSUMER_KEY', None)
CONSUMER_SECRET = getattr(settings, 'CONSUMER_SECRET', None)
 
def twitter_signin(request):
	""" Redirect user to Twitter OAuth login page. """
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	# twitter = OAuthApi(CONSUMER_KEY, CONSUMER_SECRET)
	# request_token = twitter.getRequestToken()
	# request.session['request_token'] = request_token.to_string()
	try:
		signin_url = auth.get_authorization_url()
	except tweepy.TweepError:
		print "Could not get request token!"
	request.session['request_token'] = (auth.request_token.key, auth.request_token.secret)
	return HttpResponseRedirect(signin_url)

def twitter_landing(request):
	""" Simple landing page for quick Twitter redirects. """
	request.session['verifier'] = request.GET.get('oauth_verifier')
	return render_to_response('land.html')

def confirm_OAuth(request):
	""" Pull the OAuth verifier from the user's session and authenticate."""
	
	verifier = request.session.get('verifier')
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	
	# # If there is no request_token for session,
	# #    means we didn't redirect user to twitter
	# if not request_token:
	# 	# Redirect the user to the login page,
	# 	# So the user can click on the sign-in with twitter button
	# 	return HttpResponse("HighFive didn't redirect you to Twitter. Please log in.")
	
	# Swapping request token for access_token.
	r_token = request.session.get('request_token', None)
	auth.set_request_token(r_token[0], r_token[1])
	try:
		auth.get_access_token(verifier)
		qq = auth.access_token
	except tweepy.TweepError:
		print "Error! Failed to get access token!"

	request.session['a_key'] = auth.access_token.key
	request.session['a_secret'] = auth.access_token.secret
	
	# Grabbing my a_key and a_secret for program speed testing.
	# a_key = auth.access_token.key
	# a_secret = auth.access_token.secret
	# foo
	#token = oauth.OAuthToken.from_string(request_token)

	# # If the token from session and token from twitter does not match
	# #   means something bad happened to tokens
	# if token.key != request.GET.get('oauth_token', 'no-token'):
	# 	del request.session['request_token']
	# 	# Redirect the user to the login page
	# 	# return HttpResponse('''
	# 	# <span class="title">Could not log you in! Please log in again.</span>
	# 	# ''')
	# 	return HttpResponse("Could not log you in!")

	# twitter = OAuthApi(CONSUMER_KEY, CONSUMER_SECRET, token)
	# access_token = twitter.getAccessToken()
	# 
	# # Save user info.
	# t = startAPIs(CONSUMER_KEY, CONSUMER_SECRET, access_token)
	# request.session['user'] = t.VerifyCredentials().screen_name
	# request.session['pic'] = t.VerifyCredentials().profile_image_url
	# 
	# auth_user = authenticate(access_token=access_token)
	# 
	# # if user is authenticated then login user
	# if auth_user:
	# 	login(request, auth_user)
	# 	request.session['access_token'] = access_token.to_string()
	# else:
	# 	# We were not able to authenticate user
	# 	# Redirect to login page
	# 	return HttpResponse("Unable to authenticate you!")
	# 
	return HttpResponseRedirect(reverse('links'))

def show_link_feed(request):
	""" 
	Home page view. Will perform the following via JS (jQuery):
	1. Authenticate the user and update the page title and user info.
	2. Update user's hash info.
	3. Return top 10 articles.
	"""
		
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	try:
		auth.set_access_token(request.session.get('a_key'), request.session.get('a_secret'))
	except tweepy.TweepError:
		print "Could not retrieve access token information!"

	# Update user info.
	t_api = tweepy.API(auth)
	user = t_api.verify_credentials().screen_name
	pic = t_api.verify_credentials().profile_image_url
	request.session['user'] = user
	
	return render_to_response('palm.html', {'user':user, 'pic':pic})

# def updateTitle(request):
# 	""" Update page title. """
# 	if request.is_ajax():
# 
# 		# Save user & picture info.
# 		a = request.session.get('access_token', None)
# 		a_token = oauth.OAuthToken.from_string(a)
# 		# t = startAPIs(CONSUMER_KEY, CONSUMER_SECRET, a_token)
# 		# request.session['user'] = t.VerifyCredentials().screen_name
# 		# request.session['pic'] = t.VerifyCredentials().profile_image_url
# 
# 		# Update page title.
# 		if request.session.get('user', None) != None:
# 			user = ": %s" % request.session.get('user', None)
# 			return render_to_response('title.html', {'user':user})
# 		else:
# 			return render_to_response('title.html', {'user':' '})
# 
# def getUserInfo(request):
# 	""" Get user name and picture. """
# 	if request.is_ajax():
# 		
# 		# a = request.session.get('access_token', None)
# 		# if not a:
# 		# 	raise
# 		# a_token = oauth.OAuthToken.from_string(a)
# 		# t = startAPIs(CONSUMER_KEY, CONSUMER_SECRET, a_token)
# 		# request.session['user'] = t.VerifyCredentials().screen_name
# 		# request.session['pic'] = t.VerifyCredentials().profile_image_url
# 		user = 	request.session.get('user', None)
# 		pic = request.session.get('pic', None)
# 		if not user or not pic:
# 			raise TypeError
# 	
# 		return render_to_response('info.html', {'user':user, 'pic':pic})
# 	#return render_to_response('redirect.html')

def get_hash_data(request):
	""" Sorts the data in reverse chronological order, by highest
	number of clicks. General Django rule: perform all business logic
	in views.py and not the HTML. """
	
	# if request.is_ajax():
		
	b_api = Connection('acompa', 'R_9c2643b4c8c85a250493e90ce27a624d')
		
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(request.session.get('a_key', None), request.session.get('a_secret', None))
	t_api = tweepy.API(auth)

	# Calculate the top links and store them to SQL db. Catch
	# any errors in pulling the user's info and redirect them
	# to the login page.
	user = request.session.get('user', None)
	get_highfive(b_api, t_api, user)
	hash_data = Hashdata.objects.filter(username=user).order_by("-time", "clicks")[0:5]
	results = []
	for x in hash_data:
		results.append({'title': x.title,
	                	'url': x.url,
	                	'source': x.source,
	                	'bhash': x.bhash})
	return render_to_response('palm2.html', {'results':results})

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
	
def vote_article(request):
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