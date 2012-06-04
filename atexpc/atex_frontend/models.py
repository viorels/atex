
from ancora_api.api import Ancora, MockAdapter, mock_data_path

class AncoraBackend(object):
    def __init__(self):
        mock = MockAdapter('file://%s' % mock_data_path)
        self._api = Ancora(adapter=mock)

    def get_categories(self):
        return self._api.categories()

    def get_main_categories(self):
        categories = self.get_categories()
        main_categories = [c for c in categories if c['id'].count('.') == 0]
        return main_categories

ancora = AncoraBackend()
