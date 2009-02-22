
import dapi

from products.models import Product

class ProductApi(dapi.ModelApi):
    pass

dapi.api.register(ProductApi(Product))
