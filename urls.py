from django.conf.urls.defaults import *
from django.contrib.auth.views import logout_then_login
import hi5app.views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    url(r'^highfive/l/$', hi5app.views.getHashInfo, name='l'),
    url(r'^highfive/redirect/$', hi5app.views.tempLoad, name='redirect'),
    url(r'^highfive/links/$', hi5app.views.printHashInfo, name='links'),
	(r'^hello/$', hi5app.views.hello),
	(r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
	        {'document_root': '/path/to/media'}),
	url(r'^highfive/?$', hi5app.views.printIntro, name='intro'),
	url(r'^highfive/about/$', hi5app.views.printAbout, name='about'),
	url(r'^highfive/terms/$', hi5app.views.printTerms, name='terms'),
	url(r'^highfive/help/$', hi5app.views.printHelp, name='help'),
	(r'^highfive/links/vote/$', hi5app.views.voteArticle),
	url(r'^highfive/login/$', hi5app.views.twitter_signin, name='login'),
	url(r'^highfive/logout/$', 'django.contrib.auth.views.logout_then_login'),
    url(r'^highfive/return/$', hi5app.views.twitter_return, name='return'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
