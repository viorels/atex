
from django.conf import settings
from ancora_api.api import Ancora, AncoraAdapter, MockAdapter, MOCK_DATA_PATH

class AncoraBackend(object):
    def __init__(self):
        mock = MockAdapter('file://%s' % MOCK_DATA_PATH)
        ancora = AncoraAdapter(settings.ANCORA_URI)
        self._api = Ancora(adapter=ancora)

    def get_category(self, category_id):
        all_categories = self._api.categories()
        categories = [c for c in all_categories if c['id'] == category_id]
        if len(categories) == 1:
            return categories[0]
        else:
            return None

    def get_categories(self, parent=None):
        all_categories = self._api.categories()
        categories = [c for c in all_categories if c['parent'] == parent]
        return categories

    def get_products(self, category_id=None):
        return self._api.category_products(category_id)

ancora = AncoraBackend()
