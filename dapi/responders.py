
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.http import HttpResponse
from django.utils import simplejson
from django.core.serializers.json import DjangoJSONEncoder
from django.core.handlers.wsgi import STATUS_CODE_TEXT
from django.core.xheaders import populate_xheaders
from django import forms
from django.forms.util import ErrorDict

from django.core.paginator import QuerySetPaginator, InvalidPage
from django.utils.xmlutils import SimplerXMLGenerator

_responders = {}


class Responder(object):
    def __init__(self):
        self.stream = StringIO()
    
    def handle_request(self, request, api, request_method):
        self.prepare_serialization(api.objects(request), api)
        # serialize the objects from the api
        self.serialize(api)
        return HttpResponse(self.stream.getvalue(), self.mime_type)
   
    def prepare_serialization(self, objects, api):
        self.objects = []
        for obj in objects:
            obj_data = {}
            obj_instance = api.object_class(obj)
            for field in api.fields:
                value = obj_instance.value(field)
                if hasattr(api, "prepare_%s" % field):
                    value = getattr(api, "prepare_%s" % field)(obj)
                obj_data[field] = value
            self.objects.append(obj_data)


class JSONResponder(Responder):
    """
    JSON data format class
    """
    mime_type = "application/json"

    def serialize(self, api):
        simplejson.dump(self.objects, self.stream, cls=DjangoJSONEncoder)
                

    def error(self, request, status_code, error_dict=None):
        """
        Return JSON error response that includes a human readable error
        message, application-specific errors and a machine readable
        status code.
        """
        if not error_dict:
            error_dict = ErrorDict()
        response = HttpResponse(mimetype = self.mimetype)
        response.status_code = status_code
        response_dict = {
            "error-message" : '%d %s' % (status_code, STATUS_CODE_TEXT[status_code]),
            "status-code" : status_code,
            "model-errors" : error_dict.as_ul()
        }
        simplejson.dump(response_dict, response)
        return response

def register_responder(format, responder_class):
    global _responders
    _responders[format] = responder_class

def get_responder(format):
    return _responders[format]()

# register the default responders
register_responder("json", JSONResponder)
