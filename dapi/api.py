
import re

from django.conf import settings
from django.http import HttpResponse
from django.db.models.base import ModelBase

from dapi.auth import AuthPassThru


class Api(object):
    auth = AuthPassThru()
    
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
            auth_response = self.auth.check_request(request)
            if auth_response:
                return auth_response
            response = None
            for api_instance in self._registry:
                if callable(api_instance.url):
                    url = api_instance.url()
                else:
                    url = api_instance.url
                match = url.match(rest_of_url)
                if match:
                    response = api_instance.handle_request(request)
                    break
            if response is None:
                response = HttpResponse(status=404)
            return response


class CollectionApi(object):
    """
    An API that represents a collection of objects.
    """
    
    def url(self):
        # @@@ do something sensible
        raise NotImplementedError()
    
    def handle_request(self, request):
        # @@@ serialize the return objects
        self.objects(request)
        return HttpResponse("something good happened.")
        


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
    
    def objects(self, *args, **kwargs):
        return self.queryset(*args, **kwargs)
    
    def queryset(self, request):
        return self.model._default_manager.all()

# This global object represents the default API, for the common case.
# You can instantiate Api in your own code to create a custom API.
api = Api()
