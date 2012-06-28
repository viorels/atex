
import os
import re
import json
from urlparse import urlparse, urlunparse, parse_qsl
from urllib import urlencode
from urllib2 import urlopen # TODO: try urllib3 with connection pooling
from cPickle import dumps, PicklingError # for memoize

import logging
logger = logging.getLogger(__name__)

# TODO: this doesn't work if the lib is packed in an egg
MOCK_DATA_PATH = os.path.join(os.path.split(__file__)[0], 'mock_data')

class memoize(object):
    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated. Slow for mutable types."""
    # Ideas from MemoizeMutable class of Recipe 52201 by Paul Moore and
    # from memoized decorator of http://wiki.python.org/moin/PythonDecoratorLibrary
    # For a version with timeout see Recipe 325905
    # For a self cleaning version see Recipe 440678
    # Weak references (a dict with weak values) can be used, like this:
    #   self._cache = weakref.WeakValueDictionary()
    #   but the keys of such dict can't be int
    def __init__(self, func):
        self.func = func
        self._cache = {}
    def __call__(self, *args, **kwds):
        key = args
        if kwds:
            items = kwds.items()
            items.sort()
            key = key + tuple(items)
        try:
            if key in self._cache:
                return self._cache[key]
            self._cache[key] = result = self.func(*args, **kwds)
            return result
        except TypeError:
            try:
                dump = dumps(key)
            except PicklingError:
                return self.func(*args, **kwds)
            else:
                if dump in self._cache:
                    return self._cache[dump]
                self._cache[dump] = result = self.func(*args, **kwds)
                return result

@memoize
def _read_uri(uri):
    return urlopen(uri).read()

class BaseAdapter(object):
    def __init__(self, base_uri=None):
        if not base_uri.endswith('/'):
            base_uri += '/'
        self._base_uri = base_uri

    def read(self, uri, post_process=None):
        logger.debug('>> GET %s', uri)
        response = _read_uri(uri)
        logger.debug('<< %s', response[:80])
        data = self.parse(response)
        return post_process(data) if post_process else data

    def parse(self, stream):
        return json.loads(stream)

class AncoraAdapter(BaseAdapter):
    def uri_for(self, method_name):
        args = self.args_for(method_name)
        return self.base_uri_with_args(args)

    def base_uri_with_args(self, args):
        return self.uri_with_args(self._base_uri, args)

    def uri_with_args(self, uri, new_args):
        parsed_uri = urlparse(uri)
        parsed_args = dict(parse_qsl(parsed_uri.query))
        parsed_new_args = dict(parse_qsl(new_args))
        parsed_args.update(parsed_new_args)
        final_uri = urlunparse((parsed_uri.scheme,
                                parsed_uri.netloc,
                                parsed_uri.path,
                                parsed_uri.params,
                                urlencode(parsed_args),
                                parsed_uri.fragment))
        return final_uri

    def args_for(self, method_name):
        args = {'categories': '&cod_formular=617&cfm=499'}
        return args.get(method_name)


class MockAdapter(BaseAdapter):
    def uri_for(self, method_name):
        uri = urlparse(self._base_uri)
        file_path = os.path.join(uri.path, method_name + '.json')
        return urlunparse((uri.scheme, uri.netloc, file_path, '', '', ''))


class Ancora(object):
    def __init__(self, adapter=None):
        self.adapter = adapter

    def categories(self):
        def post_process(data):
            json_root = 'gridIndex_617'
            categories = []
            for category in data.get(json_root, []):
                products_uri = self.adapter.base_uri_with_args(category['link_produse'])
                categories.append({'id': category['zcod'],
                                   'name': category['zname'],
                                   'count': category['zcount'],
                                   'parent': category['zparent'] or None,
                                   'products_uri': products_uri})
            return categories

        categories_uri = self.adapter.uri_for('categories')
        return self.adapter.read(categories_uri, post_process)

    def category_products(self, category_id):
        def post_process(data):
            json_root = 'gridIndex_618'
            products = []
            for product in data.get(json_root, []):
                thumbnail = 'images/p%02d.jpg' % (int(product['pidm']) % 4 + 1)
                products.append({'id': product['pidm'],
                                 'name': "%(zbrand)s %(zmodel)s" % product,
                                 'price': product.get('pret_catalog', 0),
                                 'old_price': str(1.1*float(product.get('pret_catalog', 0))),
                                 'stock': product['zinfo_stoc'] or 'In stoc',
                                 'thumbnail': thumbnail})
            return products

        categories = [c for c in self.categories() if c['id'] == category_id]
        if len(categories) == 1:
            products_uri = categories[0]['products_uri']
            products = self.adapter.read(products_uri, post_process)
        else:
            products = None
        return products
 
