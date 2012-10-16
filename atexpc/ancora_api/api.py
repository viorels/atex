
import os
import re
import time
import json
from urlparse import urlparse, urlunparse, parse_qsl
from urllib import urlencode
from urllib2 import urlopen # TODO: try urllib3 with connection pooling
from django.core.cache import cache

import logging
logger = logging.getLogger(__name__)

# TODO: this doesn't work if the lib is packed in an egg
MOCK_DATA_PATH = os.path.join(os.path.split(__file__)[0], 'mock_data')

TIMEOUT_LONG = 86400 # one day
TIMEOUT_NORMAL = 3600 # one hour
TIMEOUT_SHORT = 300 # 5 minutes

class BaseAdapter(object):
    def __init__(self, base_uri=None):
        self._base_uri = base_uri

    def read(self, uri, post_process=None, timeout=TIMEOUT_SHORT):
        start_time = time.time()
        response = cache.get(uri)
        cache_hit = '(cached)' if response else ''
        if response is None:
            response = urlopen(uri).read()
            cache.set(uri, response, timeout)
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
        return self.adapter.read(categories_uri, post_process, timeout=TIMEOUT_LONG)

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

        selectors_uri = self._get_category_meta(category_id, 'selectors_uri')
        if selectors_uri:
            args = {}
            if selectors_active:
                args['zvalori_selectoare_id'] = ','.join(selectors_active)
            if price_min or price_max:
                args['zpret_site_min'] = price_min
                args['zpret_site_max'] = price_max
            if args:
                selectors_uri = self.adapter.uri_with_args(selectors_uri, args)
            selectors = self.adapter.read(selectors_uri, post_process, timeout=TIMEOUT_LONG)
        else:
            selectors = []

        return selectors

    def search_products(self, category_id=None, keywords=None, selectors=None,
                        price_min=None, price_max=None, start=None, stop=None):
        def post_process(data):
            json_root = 'products'
            products = []
            for product in data.get(json_root, []):
                products.append(self._post_process_product(product))
            total_count = max(data.get('total_count', 0), len(products))
            return {'products': products,
                    'total_count': total_count}

        if category_id:
            base_products_uri = self._get_category_meta(category_id, 'products_uri')
        else:
            some_products_uri = self.categories()[0]['products_uri']
            base_products_uri = self.adapter.uri_with_args(some_products_uri,
                                                           {'idgrupa': None})

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

        products = self.adapter.read(products_uri, post_process, timeout=TIMEOUT_SHORT)
        return products

    def products_recommended(self, limit):
        def post_process(data):
            json_root = 'recommended_products'
            products = []
            for product in data.get(json_root, []):
                products.append({'id': product['zidprodus'],
                                 'model': product['zmodel'],
                                 'name': product['ztitlu'],
                                 'price': product.get('zpret_site')})
            return products

        recommended_uri = self.adapter.base_uri_with_args({
            'cod_formular': '740',
            'start': 0,
            'stop': limit})
        recommended = self.adapter.read(recommended_uri, post_process, timeout=TIMEOUT_NORMAL)
        return recommended

    def products_sales(self, limit):
        def post_process(data):
            json_root = 'promo_products'
            products = []
            for product in data.get(json_root, []):
                products.append({'id': product['zidprodus'],
                                 'model': product['zmodel'],
                                 'name': product['ztitlu'],
                                 'price': product.get('zpret_site')})
            return products

        sales_uri = self.adapter.base_uri_with_args({'cod_formular': '737',
                                                     'start': 0,
                                                     'stop': limit})
        sales = self.adapter.read(sales_uri, post_process, timeout=TIMEOUT_NORMAL)
        return sales

    def product(self, product_id):
        def post_process(data):
            json_root = 'product_info'
            product = data[json_root][0]
            return self._post_process_product(product)
            
        product_uri = self.adapter.base_uri_with_args({'cod_formular': '738',
                                                       'pidm': product_id})
        product = self.adapter.read(product_uri, post_process, timeout=TIMEOUT_SHORT)
        return product

    def _post_process_product(self, product):
        significant_price_decrease = 1.05
        if (float(product['zpret_site']) > 0
            and float(product['zpret_site_old'])/float(product['zpret_site']) 
                > significant_price_decrease):
            old_price = product['zpret_site_old']
        else:
            old_price = None

        category_code = product.get('zcod_grupa') # or zcodp for category listing
        is_available = re.match(r"[0-9.]+$", category_code) if category_code is not None else None
        stock_info = 'In stoc' if product.get('zstoc', 0) else product['zinfo_stoc_site']

        return {'id': product['pidm'],
                'model': product['zmodel'],
                'category_code': category_code,
                'name': product['ztitlu'],
                'description': product.get('zdescriere'),
                'short_description': product.get('zdescriere_scurta', ''),
                'price': product.get('zpret_site'),
                'old_price': old_price,
                'available': is_available,
                'stock': product.get('zstoc', 0),
                'stock_info': stock_info,
                'warranty': product['zluni_garantie']}

    def _get_category_meta(self, category_id, meta):
        categories = self.categories()
        found = [category for category in categories if category['id'] == category_id]
        meta_value = None
        if len(found) == 1:
            meta_value = found[0].get(meta)
        else:
            meta_value = None
            logger.warn("found %d categories with id '%s'", len(category), category_id)
        return meta_value

    def _full_text_conjunction(self, keywords):
        words = re.split(r"\s+", keywords.strip())
        conjunction = '&'.join(words)
        return conjunction
