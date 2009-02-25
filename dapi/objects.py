
from django.db import models


class CollectionObject(object):
    def __init__(self, obj):
        self.obj = obj
        
    def value(self, field):
        try:
            return self.obj[field]
        except (TypeError, KeyError):
            return getattr(self.obj, field, None)

class ModelObject(CollectionObject):
    def __init__(self, *args, **kwargs):
        super(ModelObject, self).__init__(*args, **kwargs)
        self.opts = self.obj._meta
    
    def value(self, field):
        value = super(ModelObject, self).value(field)
        model_field = self.opts.get_field(field)
        if isinstance(model_field, models.FileField):
            return value.url
        return value
