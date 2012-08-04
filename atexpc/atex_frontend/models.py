
from django.conf import settings
from atexpc.ancora_api.api import Ancora, AncoraAdapter, MockAdapter, MOCK_DATA_PATH

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

    def get_selectors(self, category_id, selectors_active):
        return self._api.selectors(category_id, selectors_active)

    def get_products(self, category_id=None, keywords=None, selectors=None,
                     start=None, stop=None):
        return self._api.search_products(category_id=category_id, keywords=keywords,
                                         selectors=selectors, start=start, stop=stop)

ancora = AncoraBackend()


