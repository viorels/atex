
import os
import re
from urlparse import urlparse, urlunparse
from urllib2 import urlopen # TODO: try urllib3 with connection pooling
import xon

mock_data_path = os.path.join(os.path.split(__file__)[0], 'mock_data')

class BaseAdapter(object):
    def __init__(self, base_uri=None):
        if not base_uri.endswith('/'):
            base_uri += '/'
        self._base_uri = base_uri

    def read(self, uri, post_process=None):
        f = urlopen(uri)
        data = xon.load(f)
        return post_process(data) if post_process else data

class AncoraAdapter(BaseAdapter):
    pass


class MockAdapter(BaseAdapter):
    def uri_for(self, method_name):
        uri = urlparse(self._base_uri)
        file_path = os.path.join(uri.path, method_name + '.xml')
        return urlunparse((uri.scheme, uri.netloc, file_path, '', '', ''))


class Ancora(object):
    def __init__(self, adapter=None):
        self.adapter = adapter

    def categories(self):
        def post_process(data):
            categories = []
            for category in data.get('tabel', {}).get('records', {}).get('row', []):
                categories.append({'id': category['@cod'],
                                   'name': re.sub(r'^[0-9.]+ ', '', category['@den']),
                                   'parent': re.sub(r'\.?[0-9]+$', '', category['@cod']) or None})
            print categories
            return categories

        uri = self.adapter.uri_for('categories')
        return self.adapter.read(uri, post_process)


