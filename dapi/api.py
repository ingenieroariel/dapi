
import re

from django.conf import settings
from django.http import HttpResponse
from django.db.models.base import ModelBase


class Api(object):
    
    def __init__(self):
        self._registry = []
            
    def register(self, api_instance):
        if not isinstance(api_instance, CollectionApi):
            if issubclass(api_instance, CollectionApi):
                api_instance = api_instance()
            else:
                raise TypeError("API instance is not an instance or subclass of CollectionApi")
        self._registry.append(api_instance)
        
    def root(self, request, url):
        url = url.rstrip("/")
        bits = url.split("/")
        
        rest_of_url = "/".join(bits[1:])
        if not rest_of_url.endswith("/"):
            rest_of_url = rest_of_url + "/"
        
        if bits[1] == "docs":
            return HttpResponse("documentation")
        else:
            response = None
            for api_instance in self._registry:
                if callable(api_instance.url):
                    url = api_instance.url()
                else:
                    url = api_instance.url
                match = url.match(rest_of_url)
                if match:
                    response = HttpResponse("found a match")
                    break
            if response is None:
                response = HttpResponse("not found")
            return response


class CollectionApi(object):
    """
    An API that represents a collection of objects.
    """
    
    def url(self):
        raise NotImplemented()


class ModelApi(CollectionApi):
    """
    A CollectionApi that knows how to work with a single given model.
    """
    
    def __init__(self, model, url_override=None):
        self.model = model
        self.opts = model._meta
        self.url_override = url_override
    
    def url(self):
        if self.url_override:
            return re.compile(self.url_override)
        return re.compile(r"^%s/%s/$" % (self.opts.app_label, self.model.__name__.lower()))

# This global object represents the default API, for the common case.
# You can instantiate Api in your own code to create a custom API.
api = Api()
