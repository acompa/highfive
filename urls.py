from django.conf.urls.defaults import *
from hi5app.views import hello, printHashInfo, printIntro, voteArticle, twitter_signin, twitter_return

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    url(r'^hi5/links/$', printHashInfo, name='links'),
	(r'^hello/$', hello),
	(r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
	        {'document_root': '/path/to/media'}),
	(r'^hi5/$', printIntro),
	(r'^hi5/vote/$', voteArticle),
	url(r'^login/$', twitter_signin, name='login'),
    url(r'^return/$', twitter_return, name='return'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
