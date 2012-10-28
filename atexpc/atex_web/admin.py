from django.contrib import admin
from models import Product
import logging

class ProductAdmin(admin.ModelAdmin):
    readonly_fields = ('model',)
admin.site.register(Product, ProductAdmin)