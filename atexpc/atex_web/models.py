
import os
import re
from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.core.files.storage import DefaultStorage
from sorl.thumbnail import ImageField
import pytz

from atexpc.ancora_api.api import Ancora, AncoraAdapter, MockAdapter, MOCK_DATA_PATH

NO_IMAGE = 'no-image'


class Dropbox(models.Model):
    app_key = models.CharField(primary_key=True, max_length=64)
    delta_cursor = models.CharField(max_length=255, blank=True, null=True)


class ProductManager(models.Manager):
    def get_top_hits(self, limit=5):
        one_month_ago = datetime.now(pytz.utc).date() - timedelta(days=30)
        return (self.filter(hit__count__gte=1,
                            hit__date__gte=one_month_ago)
                    .annotate(month_count=models.Sum('hit__count'))
                    .order_by('-month_count')[:limit])


class Product(models.Model):
    model = models.CharField(max_length=64, unique=True)
    ancora_id = models.IntegerField(null=True)

    objects = ProductManager()
    MEDIA_FOLDER = "products"

    def folder_name(self):
        folder = re.sub(r'[<>:"|?*/\\]', "-", self.model)
        return folder

    def images(self):
        images_path = os.path.join(self.MEDIA_FOLDER, self.folder_name())
        try:
            folders, image_files = DefaultStorage().listdir(images_path)
        except OSError, e:
            image_files = []
        if len(image_files):
            image_object = lambda name: Image(image=os.path.join(images_path, name))
            images = [image_object(name) for name in sorted(image_files)]
        else:
            images = [Image(image=NO_IMAGE)]
        return images

    def hit(self):
        today = datetime.now(pytz.utc).date()
        hit_info = {'count': 1}
        hit, created = Hit.objects.get_or_create(product=self, date=today,
                                                 defaults=hit_info)
        if not created:
            hit.count = models.F('count') + 1
            hit.save()


class Image(models.Model):
    def _media_path(instance, filename):
        if '/' in filename:
            path_match = re.search(r"(%s.*)" % Product.MEDIA_FOLDER, filename)
            path = path_match.group(1)
        else:
            path = os.path.join(Product.MEDIA_FOLDER, filename)
        return path
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    path = models.CharField(max_length=128, db_index=True)
    image = ImageField(upload_to=_media_path, max_length=255)


class Hit(models.Model):
    product = models.ForeignKey(Product, unique_for_date="date")
    count = models.IntegerField()
    date = models.DateField()


class AncoraBackend(object):
    def __init__(self):
        mock = MockAdapter('file://%s' % MOCK_DATA_PATH)
        ancora = AncoraAdapter(settings.ANCORA_URI)
        self._api = Ancora(adapter=ancora)

    def get_all_categories(self):
        all_valid = [category for category in self._api.categories()
                     if category['code'][0].isdecimal()] # skip "diverse" with code "XX"
        return all_valid

    def get_categories_in(self, parent=None):
        categories = [c for c in self.get_all_categories() if c['parent'] == parent]
        return categories

    def get_category(self, category_id, all_categories=None):
        if category_id is None:
            return None
        if all_categories is None:
            all_categories = self.get_all_categories()
        categories = [c for c in all_categories if c['id'] == category_id]
        if len(categories) == 1:
            return categories[0]
        else:
            return None

    def get_category_by_code(self, category_code, all_categories=None):
        if category_code is None:
            return None
        if all_categories is None:
            all_categories = self.get_all_categories()
        categories = [c for c in all_categories if c['code'] == category_code]
        if len(categories) == 1:
            return categories[0]
        else:
            return None 

    def get_parent_category(self, category_id, all_categories=None):
        if category_id is None:
            return None
        if all_categories is None:
            all_categories = self.get_all_categories()
        category = self.get_category(category_id, all_categories)
        category_code_parts = category['code'].split('.')
        parent_category_code_parts = category_code_parts[:-1]
        if parent_category_code_parts:
            parent_category_code = '.'.join(parent_category_code_parts)
            parent_categories = [c for c in all_categories if c['code'] == parent_category_code]
            if len(parent_categories) == 1:
                parent_category = parent_categories[0]
            else:
                parent_category = None
        else:
            parent_category = None
        return parent_category

    def get_top_category_id(self, category_id):
        category = self.get_category(category_id)
        parent_category_code = category['code'].split('.')[0]
        return [c for c in self.get_all_categories() if c['code'] == parent_category_code][0]['id']

    def get_selectors(self, category_id, selectors_active, price_min, price_max):
        return self._api.selectors(category_id, selectors_active,
                                   price_min=price_min, price_max=price_max)

    def get_products(self, category_id, keywords, selectors,
                     price_min, price_max, start, stop):
        return self._api.search_products(category_id=category_id, keywords=keywords,
                                         selectors=selectors, price_min=price_min,
                                         price_max=price_max, start=start, stop=stop)
    def get_product(self, product_id):
        return self._api.product(product_id)

    def get_recommended(self):
        return self._api.products_recommended()

    def get_sales(self):
        return self._api.products_sales()

ancora = AncoraBackend()


