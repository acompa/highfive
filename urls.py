from django.conf.urls.defaults import *
from django.contrib.auth.views import logout_then_login
import hi5app.views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
	url(r'^highfive/login/$', hi5app.views.twitter_signin, name='login'),
    url(r'^highfive/land/$', hi5app.views.twitter_landing, name='land'),
    url(r'^highfive/oauth/$', hi5app.views.confirm_OAuth, name='oauth'),
    url(r'^highfive/links/$', hi5app.views.show_link_feed, name='links'),
    # url(r'^highfive/title/$', hi5app.views.updateTitle, name='title'),
    # url(r'^highfive/u/$', hi5app.views.getUserInfo, name='info'),
    url(r'^highfive/d/$', hi5app.views.get_hash_data, name='d'),
    url(r'^highfive/l/(\d{1,2})/$', hi5app.views.next_10_links, name='links'),
	(r'^highfive/links/vote/$', hi5app.views.vote_article),
	(r'^hello/$', hi5app.views.hello),
	(r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
	        {'document_root': '/path/to/media'}),
	url(r'^highfive/?$', hi5app.views.print_intro, name='intro'),
	url(r'^highfive/about/$', hi5app.views.print_about, name='about'),
	url(r'^highfive/terms/$', hi5app.views.print_terms, name='terms'),
	url(r'^highfive/help/$', hi5app.views.print_help, name='help'),
	url(r'^highfive/logout/$', 'django.contrib.auth.views.logout_then_login'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
