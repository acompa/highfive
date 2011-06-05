from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User

class ModelInputs(models.Model):
	"""
	Table for recommendation model inputs and outputs for each hash
	at a given point in time.
	"""
	
	username = models.CharField(max_length=20)
	bhash = models.CharField(max_length=6)
	time = models.FloatField()
	clicks = models.IntegerField()
	cpm = models.IntegerField()
	cpd = models.IntegerField()
	timeline_count = models.IntegerField()
	source = models.CharField(max_length=20)
	score = models.IntegerField()
	
	def __unicode__(self):
		return u'%s' % self.username
	
	def vote_for_hash(self):
		self.score = 1
		self.save()	

	def up(self):
		self.score += 1
		self.save()

	def down(self):
		self.score -= 1
		self.save()

class BitlyHashInfo(models.Model):
	"""
	Table with bit.ly info on each hash. Will save queries to bit.ly
	API in the future.
	"""
	
	bhash = models.CharField(max_length=6)
	title = models.CharField(max_length=200)
	url = models.URLField()

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
