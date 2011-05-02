from django.conf.urls.defaults import *
from django.contrib.auth.views import logout_then_login
from hi5app.views import hello, getHashInfo, printHashInfo, printIntro, voteArticle, twitter_signin, twitter_return

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    url(r'^highfive/redirect/$', getHashInfo, name='redirect'),
    url(r'^highfive/links/$', printHashInfo, name='links'),
	(r'^hello/$', hello),
	(r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
	        {'document_root': '/path/to/media'}),
	url(r'^highfive/?$', printIntro, name='intro'),
	(r'^highfive/links/vote/$', voteArticle),
	url(r'^highfive/login/$', twitter_signin, name='login'),
	url(r'^highfive/logout/$', 'django.contrib.auth.views.logout_then_login'),
    url(r'^highfive/return/$', twitter_return, name='return'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
