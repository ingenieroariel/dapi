
import dapi
from dapi.responders import JSONResponder

from products.models import Product

class ProductApi(dapi.ModelApi):
    responder_class = JSONResponder
    fields = ["name"]

dapi.default_api.register(ProductApi(Product))
