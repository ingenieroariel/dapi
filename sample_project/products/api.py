
import dapi
from dapi.responders import JSONResponder

from products.models import Product

class ProductApi(dapi.ModelApi):
    responder_class = JSONResponder
    fields = ["name", "slug", "description", "creation_date",
            "is_cool", "discount", "price" ]

dapi.default_api.register(ProductApi(Product))
