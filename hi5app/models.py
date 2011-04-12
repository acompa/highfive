from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User

class Hashdata(models.Model):
	""" Data in MySQL for each bit.ly hash. Add 'user' to this soon. """
	name = models.CharField(max_length=6)
	title = models.CharField(max_length=200)
	url = models.URLField()
	time = models.FloatField()        #seconds since epoch
	clicks = models.IntegerField()
	cpm = models.FloatField()
	cpd = models.FloatField()
	source = models.CharField(max_length=15)
	score = models.IntegerField()
	
	def __unicode__(self):
		return self.name

class UserProfile(models.Model):
	user = models.ForeignKey(User)
	access_token = models.CharField(max_length=255, blank=True, null=True, editable=False)
	# access_token_key = models.CharField(max_length=255, blank=True, null=True, editable=False)
	# access_token_secret = models.CharField(max_length=255, blank=True, null=True, editable=False)
	profile_image_url = models.URLField(blank=True, null=True)
	location = models.CharField(max_length=100, blank=True, null=True)
	url = models.URLField(blank=True, null=True)
	description = models.CharField(max_length=160, blank=True, null=True)

	def __str__(self):
		return "%s's profile" % self.user

def create_user_profile(sender, instance, created, **kwargs):
	if created:
		profile, created = UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User)
