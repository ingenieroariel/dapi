
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)    
    slug = models.SlugField()
    description = models.TextField()
    quantity = models.IntegerField()
    is_cool = models.BooleanField()
    creation_date = models.DateTimeField()
    image = models.ImageField(upload_to='products')
    discount = models.DecimalField(max_digits=3, decimal_places=2)
    price = models.FloatField()
