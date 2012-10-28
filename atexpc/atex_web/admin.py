from django.contrib import admin
from models import Product
import logging

#logger = logging.getLogger(__name__)
#logger.error('Something went wrong!')

class ProductAdmin(admin.ModelAdmin):
    pass



admin.site.register(Product, ProductAdmin)