
import dapi
from dapi.responders import JSONResponder

from products.models import Product

class ProductApi(dapi.ModelApi):
    responder_class = JSONResponder
    fields = ["name", "slug", "description", "creation_date",
              "is_cool", "discount", "price", "image", "vendor" ]

    # Sample serialization override for a given field
#    def prepare_image(self, obj):
#        return obj.image.url

dapi.default_api.register(ProductApi(Product))
