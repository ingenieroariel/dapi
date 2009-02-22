from django.conf.urls.defaults import *

import dapi
dapi.autodiscover()

from django.contrib import admin
admin.autodiscover()

from sample_project.api import oauth_api


urlpatterns = patterns('',
    url(r'^admin/(.*)', admin.site.root),
    url(r'^api/(.*)', dapi.default_api.root),
)

try:
    import oauth
    import oauth_provider
except ImportError:
    oauth_support = False
else:
    oauth_support = True

if oauth_support:
    urlpatterns += patterns('',
        url(r'oauth/', include('oauth_provider.urls')),
        url(r'oauth_api/(.*)', oauth_api.root),
    )
