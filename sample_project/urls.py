from django.conf.urls.defaults import *

import dapi
dapi.autodiscover()

from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    url(r'^admin/(.*)', admin.site.root),
    url(r'^api/(.*)', dapi.api.root),
)
