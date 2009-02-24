
from django.contrib import admin

from products.models import Product

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description', 'quantity', 'is_cool',
    'creation_date', 'image', 'discount', 'price')

admin.site.register(Product, ProductAdmin)
