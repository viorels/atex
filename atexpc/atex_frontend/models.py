
from django.conf import settings
from django.db import models
from sorl.thumbnail import ImageField
from atexpc.ancora_api.api import Ancora, AncoraAdapter, MockAdapter, MOCK_DATA_PATH

class Product(models.Model):
    model = models.CharField(max_length=64)

class Image(models.Model):
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    image = ImageField(upload_to='product-images', max_length=128)

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

    def get_category(self, category_id):
        categories = [c for c in self.get_all_categories() if c['id'] == category_id]
        if len(categories) == 1:
            return categories[0]
        else:
            return None

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

ancora = AncoraBackend()


