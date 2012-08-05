
import os
import re
import time
import json
from urlparse import urlparse, urlunparse, parse_qsl
from urllib import urlencode
from urllib2 import urlopen # TODO: try urllib3 with connection pooling
from collections import OrderedDict
from django.core.cache import cache

import logging
logger = logging.getLogger(__name__)

# TODO: this doesn't work if the lib is packed in an egg
MOCK_DATA_PATH = os.path.join(os.path.split(__file__)[0], 'mock_data')


class BaseAdapter(object):
    def __init__(self, base_uri=None):
        self._base_uri = base_uri

    def read(self, uri, post_process=None):
        start_time = time.time()
        response = cache.get(uri)
        cache_hit = '(cached)' if response else ''
        if response is None:
            response = urlopen(uri).read()
            cache.set(uri, response)
        elapsed = time.time() - start_time
        logger.debug('GET%s %s (%s bytes in %1.3f seconds)', 
                     cache_hit, uri, len(response), elapsed)
        data = self.parse(response)
        return post_process(data) if post_process else data

    def parse(self, stream):
        try:
            return json.loads(stream)
        except ValueError, e:
            logger.error("failed to parse backend response: %s", e)
            return {'error': 'failed to parse backend response'}


class AncoraAdapter(BaseAdapter):
    def uri_for(self, method_name):
        args = self.args_for(method_name)
        return self.base_uri_with_args(args)

    def base_uri_with_args(self, args):
        return self.uri_with_args(self._base_uri, args)

    def uri_with_args(self, uri, new_args):
        parsed_uri = urlparse(uri)

        parsed_args = dict(parse_qsl(parsed_uri.query))
        parsed_new_args = dict(parse_qsl(new_args)) if isinstance(new_args, basestring) else new_args
        parsed_args.update(parsed_new_args)
        valid_args = dict((key, value) for key, value in parsed_args.items() if value is not None)
        encoded_args = urlencode(valid_args)

        final_uri = urlunparse((parsed_uri.scheme,
                                parsed_uri.netloc,
                                parsed_uri.path,
                                parsed_uri.params,
                                encoded_args,
                                parsed_uri.fragment))
        return final_uri

    def args_for(self, method_name):
        args = {'categories': '&cod_formular=617'}
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
            json_root = 'categories'
            categories = []
            for category in data.get(json_root, []):
                categories.append({'id': category['pidm'],
                                   'code': category['zcod'],
                                   'name': category['zname'],
                                   'count': category['zcount'],
                                   'parent': category['zparent'] or None,
                                   'products_uri': category['link_produse'],
                                   'selectors_uri': category['link_selectoare']})
            return categories

        categories_uri = self.adapter.uri_for('categories')
        return self.adapter.read(categories_uri, post_process)

    def selectors(self, category_id, selectors_active, price_min, price_max):
        def post_process(data):
            json_root = 'selectors'
            selectors = []
            for selector_group in data.get(json_root, []):
                items = [{'selector_id': item['zid'], 'name': item['zdenumire'],
                          'count': item['zcount']}
                         for item in selector_group['zvalori_posibile']]
                selectors.append({'name': selector_group['zdenumire'],
                                  'selectors': items,
                                  })
            return selectors            

        categories = self.categories()
        category = [c for c in categories if c['id'] == category_id]
        if len(category) == 1:
            selectors_uri = category[0]['selectors_uri']
            args = {}
            if selectors_active:
                args['zvalori_selectoare_id'] = ','.join(selectors_active)
            if price_min or price_max:
                args['zpret_site_min'] = price_min
                args['zpret_site_max'] = price_max
            if args:
                selectors_uri = self.adapter.uri_with_args(selectors_uri, args)
            selectors = self.adapter.read(selectors_uri, post_process)
        else:
            logger.warn("found %d categories with id '%s'", len(category), category_id)
            selectors = []

        return selectors

    def search_products(self, category_id=None, keywords=None, selectors=None,
                        price_min=None, price_max=None, start=None, stop=None):
        def post_process(data):
            json_root = 'products'
            products = []
            for product in data.get(json_root, []):
                thumbnail = 'images/p%02d.jpg' % (int(product['pidm']) % 4 + 1)
                significant_price_decrease = 1.05
                old_price = (product['zpret_site_old']
                             if float(product['zpret_site_old'])/float(product['zpret_site']) 
                                > significant_price_decrease
                             else None)
                products.append({'id': product['pidm'],
                                 'model': product['zmodel'],
                                 'name': "%(zbrand)s %(zmodel)s" % product,
                                 'price': product.get('zpret_site'),
                                 'old_price': old_price,
                                 'stock': product['zinfo_stoc_site'],
                                 'warranty': product['zluni_garantie'],
                                 'thumbnail': thumbnail})
            total_count = max(data.get('total_count', 0), len(products))
            return {'products': products,
                    'total_count': total_count}

        base_products_uri = None
        categories = self.categories()
        if category_id:
            category = [c for c in categories if c['id'] == category_id]
            if len(category) == 1:
                base_products_uri = category[0]['products_uri']
        if not base_products_uri:
            some_products_uri = categories[0]['products_uri']
            base_products_uri = self.adapter.uri_with_args(some_products_uri, {'idgrupa': None})

        args = {'start': start,
                'stop': stop}
        if selectors:
            args['zvalori_selectoare_id'] = ','.join(selectors)
        if keywords:
            args['zdescriere'] = self._full_text_conjunction(keywords)
        if price_min or price_max:
            args['zpret_site_min'] = price_min
            args['zpret_site_max'] = price_max
        products_uri = self.adapter.uri_with_args(base_products_uri, args)

        products = self.adapter.read(products_uri, post_process)
        return products
 
    def _full_text_conjunction(self, keywords):
        words = re.split(r"\s+", keywords)
        conjunction = '&'.join(words)
        return conjunction