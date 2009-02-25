
import re

from django.conf import settings
from django.http import HttpResponse
from django.db.models.base import ModelBase

from dapi.auth import NoAuthentication
from dapi.responders import get_responder
from dapi.objects import CollectionObject, ModelObject

from django.utils.translation import ugettext as _
from django.forms.util import ErrorDict

from django.core.urlresolvers import reverse as _reverse
from django.http import Http404, HttpResponse, HttpResponseNotAllowed

class InvalidModelData(Exception):
    """
    Raised if create/update fails because the PUT/POST 
    data is not appropriate.
    """
    def __init__(self, errors=None):
        if not errors:
            errors = ErrorDict()
        self.errors = errors


def load_put_and_files(request):
    """
    Populates request.PUT and request.FILES from
    request.raw_post_data. PUT and POST requests differ
    only in REQUEST_METHOD, not in the way data is encoded.
    Therefore we can use Django's POST data retrieval method
    for PUT.
    """
    if request.method == 'PUT':
        request.method = 'POST'
        request._load_post_and_files()
        request.method = 'PUT'
        request.PUT = request.POST
        del request._post

def reverse(viewname, args=(), kwargs=None):
    """
    Return the URL associated with a view and specified parameters.
    If the regular expression used specifies an optional slash at
    the end of the URL, add the slash.
    """
    if not kwargs:
        kwargs = {}
    url = _reverse(viewname, None, args, kwargs)
    if url[-2:] == '/?':
        url = url[:-1]
    return url

class HttpMethodNotAllowed(Exception):
    """
    Signals that request.method was not part of
    the list of permitted methods.
    """


class Api(object):
    
    def __init__(self, extends=None, authentication=NoAuthentication(), permitted_methods=None):
        self._registry = []
        # inheritance of another api
        """
        extends:
            the base api class to inherit from
        authentication:
            the authentication instance that checks whether a
            request is authenticated
        permitted_methods:
            the HTTP request methods that are allowed for this
            resource e.g. ('GET', 'PUT')
        """
        self.authentication = authentication

        if not permitted_methods:
            permitted_methods = ["GET"]
        self.permitted_methods = [m.upper() for m in permitted_methods]

        if extends is not None:
            self._registry.extend(extends._registry)
 
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
        
        rest_of_url = "/".join(bits)
        if not rest_of_url.endswith("/"):
            rest_of_url = rest_of_url + "/"

        if rest_of_url != '/' and bits[1] == "docs":
            return HttpResponse("documentation")
        else:
            return self.dispatch(request, rest_of_url)
    
    def dispatch(self, request, url):
        request_method = request.method.upper()
        if request_method not in self.permitted_methods:
            raise HttpMethodNotAllowed

        auth_response = self.authentication.check_request(request)
        if auth_response:
            return auth_response
        response = None
        for api_instance in self._registry:
            if callable(api_instance.url):
                url_regex = api_instance.url()
            else:
                url_regex = api_instance.url
            match = re.match(url_regex, url)
            if match:
                format = match.groupdict().get("format")
                response = api_instance.handle_request(request, request_method, format)
                break
        if response is None:
            response = HttpResponse(status=404)
        return response


class CollectionApi(object):
    """
    An API that represents a collection of objects.
    """
    object_class = CollectionObject
    
    def url(self):
        # @@@ do something sensible
        raise NotImplementedError()
    
    def handle_request(self, request, request_method=None, format=None):
        if format is None:
            responder = self.responder_class()
        else:
            responder = get_responder(format)
        return responder.handle_request(request, self, request_method)
        

class ModelApi(CollectionApi):
    """
    A CollectionApi that knows how to work with a single given model.
    """
    object_class = ModelObject
    
    def __init__(self, model, url=None):
        self.model = model
        self.opts = model._meta
        self.url_override = url
    
    def url(self):
        if self.url_override:
            return self.url_override
        return r"^%s/%s(\.(?P<format>[a-z]*)|)/$" % (self.opts.app_label, self.model.__name__.lower())
    
    def objects(self, *args, **kwargs):
        return self.queryset(*args, **kwargs).iterator()
    
    def queryset(self, request):
        return self.model._default_manager.all()

    def create(self, request):
        """
        Creates a resource with attributes given by POST, then
        redirects to the resource URI. 
        """
        # Create form filled with POST data
        ResourceForm = models.modelform_factory(self.queryset.model, form=self.form_class)
        data = self.receiver.get_post_data(request)
        form = ResourceForm(data)
        
        # If the data contains no errors, save the model,
        # return a "201 Created" response with the model's
        # URI in the location header and a representation
        # of the model in the response body.
        if form.is_valid():
            new_model = form.save()
            model_entry = self.entry_class(self, new_model)
            response = model_entry.read(request)
            response.status_code = 201
            response['Location'] = model_entry.get_url()
            return response

        # Otherwise return a 400 Bad Request error.
        raise InvalidModelData(form.errors)


    def get_entry(self, pk_value):
        """
        Returns a single entry retrieved by filtering the 
        collection queryset by primary key value.
        """
        model = self.queryset.get(**{self.queryset.model._meta.pk.name : pk_value})
        entry = self.entry_class(self, model)
        return entry



class Entry(object):
    """
    Resource for a single model.
    """

    def __init__(self, collection, model, url=None):
        self.model = model
        self.opts = model._meta
        self.collection = collection
        self.url_override = url
       
    def url(self):
        """
        Returns the URL for this resource object.
        """
        if self.url_override:
            return self.url_override
 
        pk_value = getattr(self.model, self.model._meta.pk.name)
        return reverse(self.collection, (pk_value,))
   
    def create(self, request):
        raise Http404
   
    def read(self, request):
        """
        Returns a representation of a single model.
        The format depends on which responder (e.g. JSONResponder)
        is assigned to this ModelResource instance. Usually called by a
        HTTP request to the resource URI with method GET.
        """
        return self.collection.responder.element(request, self.model)
   
    def update(self, request):
        """
        Changes the attributes of the resource identified by 'ident'
        and redirects to the resource URI. Usually called by a HTTP
        request to the resource URI with method PUT.
        """
        # Create a form from the model/PUT data
        ResourceForm = models.modelform_factory(self.model.__class__, 
                                     form=self.collection.form_class)

        data = self.collection.receiver.get_put_data(request)

        form = ResourceForm(data, instance=self.model)       
       
        # If the data contains no errors, save the model,
        # return a "200 Ok" response with the model's
        # URI in the location header and a representation
        # of the model in the response body.
        if form.is_valid():
            form.save()
            response = self.read(request)
            response.status_code = 200
            response['Location'] = self.get_url()
            return response
       
        # Otherwise return a 400 Bad Request error.
        raise InvalidModelData(form.errors)
   
    def delete(self, request):
        """
        Deletes the model associated with the current entry.
        Usually called by a HTTP request to the entry URI
        with method DELETE.
        """
        self.model.delete()
        return HttpResponse(_("Object successfully deleted."), self.collection.responder.mimetype)
    

# This global object represents the default API, for the common case.
# You can instantiate Api in your own code to create a custom API.
default_api = Api()
