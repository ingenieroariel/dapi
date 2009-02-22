
import dapi

from products.models import Product

class ProductApi(dapi.ModelApi):
    pass

dapi.default_api.register(ProductApi(Product))
