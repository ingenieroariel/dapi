from django.conf.urls.defaults import *
from django.conf import settings
import os.path

import dapi
dapi.autodiscover()

from django.contrib import admin
admin.autodiscover()


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
    from sample_project.api import oauth_api
    
    urlpatterns += patterns('',
        url(r'oauth/', include('oauth_provider.urls')),
        url(r'oauth_api/(.*)', oauth_api.root),
    )

if settings.SERVE_MEDIA:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': os.path.join(os.path.dirname(__file__), "site_media")}),
    )
