import re

from django.conf import settings
from django.http import HttpResponse
from django.db.models.base import ModelBase

from dapi import ModelApi


class Api(object):
    
    def __init__(self):
        self._registry = {} # model_class class -> api_class instance
        # TODO Root path is used to calculate urls under the old root() method
        # in order to maintain backwards compatibility we are leaving that in
        # so root_path isn't needed, not sure what to do about this.
        self.root_path = 'api/'
            
    def register(self, model_or_iterable, api_class=None, **options):  
          """
          Registers the given model(s) with the given api class.
            
          The model(s) should be Model classes, not
          instances.
  
          If an api class isn't given, it will use ModelAdmin (the default
          api options). If keyword arguments are given -- e.g., list_display --
          they'll be applied as options to the api class.
            
          If a model is already registered, this will raise AlreadyRegistered.
          """
          if not api_class:
              api_class = ModelApi
          if isinstance(model_or_iterable, ModelBase):
               model_or_iterable = [model_or_iterable]
          for model in model_or_iterable:
              if model in self._registry:
                  raise AlreadyRegistered('The model %s is already registered' % model.__name__)
              self._registry[model] = api_class(model, self)

    def unregister(self, model_or_iterable):
        """
        Unregisters the given model(s).

        If a model isn't already registered, this will raise NotRegistered.
        """
        if isinstance(model_or_iterable, ModelBase):
                model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if model not in self._registry:
                raise NotRegistered('The model %s is not registered' % model.__name__)
            del self._registry[model]
        
    def root(self, request, url):
        return HttpResponse("hello world")
 
# This global object represents the default API, for the common case.
# You can instantiate Api in your own code to create a custom API.
site = Api()
