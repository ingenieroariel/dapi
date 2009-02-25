
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.http import HttpResponse
from django.utils import simplejson
from django.core.serializers.json import DjangoJSONEncoder


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
    mime_type = "application/json"
    
    def serialize(self, api):
        simplejson.dump(self.objects, self.stream, cls=DjangoJSONEncoder)


def register_responder(format, responder_class):
    global _responders
    _responders[format] = responder_class

def get_responder(format):
    return _responders[format]()

# register the default responders
register_responder("json", JSONResponder)
