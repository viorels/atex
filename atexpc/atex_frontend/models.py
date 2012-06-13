
from ancora_api.api import Ancora, MockAdapter, mock_data_path

class AncoraBackend(object):
    def __init__(self):
        mock = MockAdapter('file://%s' % mock_data_path)
        self._api = Ancora(adapter=mock)

    def get_categories(self, parent=None):
        all_categories = self._api.categories()
        categories = [c for c in all_categories if c['parent'] == parent]
        return categories

ancora = AncoraBackend()
