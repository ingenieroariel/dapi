from django.conf.urls.defaults import *

import dapi
dapi.autodiscover()

from django.contrib import admin
admin.autodiscover()

from sample_project.api import oauth_api


urlpatterns = patterns('',
    url(r'^admin/(.*)', admin.site.root),
    url(r'^api/(.*)', dapi.api.root),
    url(r'oauth_api/(.*)', oauth_api.root),
)
