import os
import re
import time
import hashlib
import json
import operator
import bcrypt
from urlparse import urlparse, urlunparse, parse_qsl
from urllib import urlencode
from django.core.cache import cache as django_cache

import requests
from requests.exceptions import ConnectionError, Timeout

import logging
logger = logging.getLogger(__name__)

# TODO: this doesn't work if the lib is packed in an egg
MOCK_DATA_PATH = os.path.join(os.path.split(__file__)[0], 'mock_data')

TIMEOUT_LONG = 86400    # one day
TIMEOUT_NORMAL = 3600   # one hour
TIMEOUT_SHORT = 300     # 5 minutes
TIMEOUT_NO_CACHE = 0    # do not cache


class APIError(Exception):
    pass


class BaseAdapter(object):
    def __init__(self, base_uri=None, cache=django_cache, use_backend=None):
        """ - base_uri = common part of the API uri
            - use_backend = None: try cache and fallback to backend
                            True: always use backend
                            False: never use backend"""
        self._base_uri = base_uri
        self._cache = cache
        self._use_backend = use_backend
        self._requests = requests.session()  # TODO: thread safe ?

    def _cache_key(self, uri):
        cache_key = self.normalize_uri(uri)
        if len(cache_key) > 250:
            cache_key = hashlib.sha1(cache_key).hexdigest()
        return cache_key

    def _read_cache(self, uri):
        if self._cache:
            return self._cache.get(self._cache_key(uri))

    def _write_cache(self, uri, data, timeout):
        if self._cache:
            self._cache.set(self._cache_key(uri), data, timeout)

    def _read_backend(self, uri):
        raise NotImplemented()

    def _write_backend(self, uri, data):
        raise NotImplemented()

    def read(self, uri, post_process=None, use_backend=None, cache_timeout=TIMEOUT_SHORT):
        """ Read data from backend and cache processed data
            - uri to fetch data from, can be a http url or a file path
            - use_backend = None: try cache and fallback to backend
                            True: always use backend
                            False: never use backend"""
        if use_backend is None:
            use_backend = self._use_backend

        start_time = time.time()

        if use_backend is not True:
            cache_response = self._read_cache(uri)  # returns None if item not found
        else:
            cache_response = None
        if cache_response is None and use_backend is not False:
            response = self._read_backend(uri)
            data = self.parse(response)
            processed_data = post_process(data) if post_process else data
            if cache_timeout != TIMEOUT_NO_CACHE:
                self._write_cache(uri, processed_data, timeout=cache_timeout)
        else:
            processed_data = cache_response

        self._read_debug(uri, cache_response, locals().get('response'), start_time)

        return processed_data

    def write(self, uri, data, post_process=None):
        response = self._write_backend(uri, data)
        return post_process(response) if post_process is not None else response

    def _read_debug(self, uri, cache_response, response, start_time):
        elapsed = time.time() - start_time
        if cache_response is not None:
            stats = '(cache)'
        elif response is not None:
            stats = '(%s bytes in %1.3f seconds)' % (len(response), elapsed)
        else:
            stats = ''
        logger.debug('GET %s %s', self.normalize_uri(uri), stats)

    def parse(self, stream):
        try:
            return json.loads(stream)
        except ValueError as e:
            message = "We failed to parse backend response: %s" % e
            logger.error(message)
            raise APIError(message)

    def normalize_uri(self, uri):
        """ Normalize uri by sorting argumenst """
        parsed_uri = urlparse(uri)
        parsed_args = parse_qsl(parsed_uri.query)
        sorted_parsed_args = sorted(parsed_args, key=operator.itemgetter(0))
        sorted_args = urlencode(sorted_parsed_args)
        return urlunparse((parsed_uri.scheme,
                           parsed_uri.netloc,
                           parsed_uri.path,
                           parsed_uri.params,
                           sorted_args,
                           parsed_uri.fragment))


class AncoraAdapter(BaseAdapter):
    def __init__(self, *args, **kwargs):
        default_api_timeout = 10  # seconds
        self._api_timeout = kwargs.pop('api_timeout') if 'api_timeout' in kwargs else default_api_timeout
        super(AncoraAdapter, self).__init__(*args, **kwargs)

    def _read_backend(self, uri):
        try:
            response = self._requests.get(self.normalize_uri(uri), timeout=self._api_timeout)
            return response.text
        except (ConnectionError, Timeout) as e:
            raise APIError("Failed to reach backend (%s)" % type(e).__name__)

    def _write_backend(self, uri, data):
        try:
            response = self._requests.post(uri, data=data, timeout=self._api_timeout)
            return response.text
        except (ConnectionError, Timeout) as e:
            raise APIError("Failed to reach backend (%s)" % type(e).__name__)

    def uri_for(self, method_name, args={}):
        all_args = self._args_for(method_name)
        all_args.update(args)
        return self.uri_with_args(self._base_uri,
                                  method=self._method_for(method_name),
                                  args=all_args)

    def _method_for(self, method_name):
        default_path = 'jis.serv'
        post_path = 'saveForm.do'
        if re.match(r'create|update', method_name):
            method = post_path
        else:
            method = default_path
        return method

    def _args_for(self, method_name):
        args = {'categories': {'cod_formular': '617'},
                'product': {'cod_formular': '738'},
                'recommended': {'cod_formular': '740', 'start': '0'},
                'promotional': {'cod_formular': '737', 'start': '0'},
                'brands': {'cod_formular': '1024', 'start': '0', 'stop': '1000'},
                'create_user': {'cod_formular': '1312',
                                'pid': '0',         # new user
                                'iduser': '47',     # website user
                                'actiune': 'SAVE_TAB'},
                'get_user': {'cod_formular': '1023'},
                'list_cart': {'cod_formular': '1078'},
                'create_cart': {'cod_formular': '1366',
                                'pid': '0',
                                'iduser': '47',
                                'actiune': 'SAVE_TAB'},
                'create_cart_entry': {'cod_formular': '1367',
                                      'pid': '0',
                                      'actiune': 'SAVE_TAB'}}
        return args.get(method_name, {})

    def uri_with_args(self, uri, method=None, args=None):
        parsed_uri = urlparse(uri)

        if method is not None:
            delimiter = '/'
            path_parts = parsed_uri.path.split(delimiter)
            path = delimiter.join(path_parts[:-1] + [method])
        else:
            path = parsed_uri.path

        parsed_old_args = dict(parse_qsl(parsed_uri.query))
        parsed_args = dict(parse_qsl(args)) if isinstance(args, basestring) else args
        parsed_old_args.update(parsed_args)
        valid_args = dict((key, value) for key, value in parsed_old_args.items() if value is not None)
        encoded_args = urlencode(valid_args)

        final_uri = urlunparse((parsed_uri.scheme,
                                parsed_uri.netloc,
                                path,
                                parsed_uri.params,
                                encoded_args,
                                parsed_uri.fragment))
        return final_uri


class MockAdapter(BaseAdapter):
    def __init__(self, base_uri=MOCK_DATA_PATH, **kwargs):
        super(MockAdapter, self).__init__(base_uri, **kwargs)

    def _read_backend(self, uri):
        return open(uri).read()

    def uri_for(self, method_name, args={}):
        file_name = self._file_name_for(method_name, args)
        return os.path.join(self._base_uri, file_name)

    def _file_name_for(self, method_name, args):
        name_generator = {
            'product': lambda: "%s_%s" % (method_name, args['pidm'])
        }
        default_generator = lambda: method_name
        name = name_generator.get(method_name, default_generator)()
        return name + '.json'


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
        return self.adapter.read(categories_uri, post_process,
                                 cache_timeout=TIMEOUT_LONG) or []

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
                selectors_uri = self.adapter.uri_with_args(selectors_uri, args=args)
            selectors = self.adapter.read(selectors_uri, post_process, cache_timeout=TIMEOUT_LONG)
        else:
            selectors = []

        return selectors

    def _base_products_uri(self, category_id=None):
        if category_id:
            base_products_uri = self._get_category_meta(category_id, 'products_uri')
        else:
            some_products_uri = self.categories()[0]['products_uri']
            base_products_uri = self.adapter.uri_with_args(some_products_uri,
                                                           args={'idgrupa': None})
        return base_products_uri

    def _post_process_product_list(self, json_root='products'):
        def post_process(data):
            products = []
            for product in data.get(json_root, []):
                products.append(self._post_process_product(product))
            total_count = max(data.get('total_count', 0), len(products))
            return {'products': products,
                    'total_count': total_count}
        return post_process

    def _no_products(self):
        return self._post_process_product_list()({})

    def search_products(self, category_id=None, keywords=None, selectors=None,
                        price_min=None, price_max=None, start=None, stop=None,
                        stock=None, sort_by=None, sort_order=None):
        if not (keywords or selectors or 
                (category_id and self._base_products_uri(category_id))):
            return self._no_products()

        args = {'start': start,
                'stop': stop}
        if selectors:
            args['zvalori_selectoare_id'] = ','.join(selectors)
        if keywords:
            args['zdescriere'] = self._full_text_conjunction(keywords)
        if price_min or price_max:
            args['zpret_site_min'] = price_min
            args['zpret_site_max'] = price_max
        if stock:
            args['zstoc'] = 'D'
        if sort_by:
            args['zsort'] = {'pret': 'zpret_site'}.get(sort_by, '')
            args['zsort_order'] = sort_order
        products_uri = self.adapter.uri_with_args(
            self._base_products_uri(category_id),
            args=args)

        products = self.adapter.read(products_uri,
                                     self._post_process_product_list(),
                                     cache_timeout=TIMEOUT_SHORT)
        return products

    def products_recommended(self, limit):
        recommended_uri = self.adapter.uri_for('recommended', {'stop': limit})
        recommended = self.adapter.read(
            recommended_uri,
            self._post_process_product_list(json_root='recommended_products'),
            cache_timeout=TIMEOUT_NORMAL)
        return recommended

    def products_promotional(self, limit):
        promotional_uri = self.adapter.uri_for('promotional', {'stop': limit})
        promotional = self.adapter.read(
            promotional_uri,
            self._post_process_product_list(json_root='promo_products'),
            cache_timeout=TIMEOUT_NORMAL)
        return promotional

    def product_list(self, product_ids):
        args = {'zlista_id': ','.join(str(pid) for pid in product_ids)}
        products_uri = self.adapter.uri_with_args(
            self._base_products_uri(),
            args=args)
        products = self.adapter.read(products_uri,
                                     self._post_process_product_list(),
                                     cache_timeout=TIMEOUT_SHORT)
        return products

    def product(self, product_id):
        def post_process(data):
            json_root = 'product_info'
            product = data[json_root][0] if len(data[json_root]) else None
            return self._post_process_product(product) if product else None

        product_uri = self.adapter.uri_for('product', {'pidm': product_id})
        product = self.adapter.read(product_uri, post_process, cache_timeout=TIMEOUT_SHORT)
        return product

    def _post_process_product(self, product):
        significant_price_decrease = 1.05
        if (float(product['zpret_site']) > 0
            and float(product.get('zpret_site_old', 0)) / float(product['zpret_site'])
                > significant_price_decrease):
            old_price = product['zpret_site_old']
        else:
            old_price = None

        category_code = product.get('zcod_grupa') or product.get('zcodp')
        is_available = bool(re.match(r"[0-9.]+$", category_code)) if category_code is not None else False
        stock_info = 'In stoc' if product.get('zstoc', 0) else product.get('zinfo_stoc_site', '')

        return {'id': product.get('pidm') or product.get('zidprodus'),
                'brand': product.get('zbrand'),
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
                'warranty': product.get('zluni_garantie'),
                'properties': self._product_properties(product.get('zselectori', []))}

    def _product_properties(self, selectors):
        properties = {}
        for selector in selectors:
            properties[selector['zdenumire']] = selector['zvalori']
        return properties

    def _get_category_meta(self, category_id, meta):
        categories = self.categories()
        found = [category for category in categories if category['id'] == category_id]
        meta_value = None
        if len(found) == 1:
            meta_value = found[0].get(meta)
        else:
            meta_value = None
            logger.warn("found %d categories with id '%s'", len(found), category_id)
        return meta_value

    def _full_text_conjunction(self, keywords):
        words = re.split(r"\s+", keywords.strip())
        conjunction = '&'.join(words)
        return conjunction

    def brands(self):
        def post_process(data):
            json_root = 'brands'
            brands = [brand['zdenumire'].capitalize() for brand in data.get(json_root, [])]
            return brands

        brands_uri = self.adapter.uri_for('brands')
        return self.adapter.read(brands_uri, post_process,
                                 cache_timeout=TIMEOUT_LONG) or []

    @staticmethod
    def _post_process_write(data):
        return data.splitlines[1]

    def create_user(self, email, first_name, last_name, password, usertype, salt=None):
        create_user_uri = self.adapter.uri_for('create_user')
        args = {'email': email,
                'denumire': "%s %s" % (last_name, first_name),
                'parola': self._password_hash(password, salt),
                'fj': usertype}
        return self.adapter.write(create_user_uri, args, post_process=self._post_process_write)

    def get_user(self, email, password, salt=None):
        """ Returns a user if the password is good, otherwise None """
        def post_process(data):
            json_root = 'useri_site'
            backend_user = data[json_root][0] if len(data[json_root]) else None
            if backend_user is not None:
                last_name, first_name = backend_user['zdenumire'].split(" ", 1)
                user = {'email': backend_user['zemail'],
                        'first_name': first_name,
                        'last_name': last_name,
                        'usertype': backend_user['zfj'],            # F/J
                        'disabled': backend_user['zcol_inactiv'] == 'Y'}   # Y/N
            else:
                user = None
            return user

        args = {'femail': email,
                'fparola': self._password_hash(password, salt)}
        get_user_uri = self.adapter.uri_for('get_user', args)
        user = self.adapter.read(get_user_uri, post_process=post_process, cache_timeout=TIMEOUT_SHORT)
        user['password'] = self._password_hash(password, salt)
        return user

    def _password_hash(self, password, salt=None):
        if salt is None:
            salt = bcrypt.gensalt()
        return bcrypt.hashpw(password, salt)

    def create_cart(self, user_id):
        create_cart_uri = self.adapter.uri_for('create_cart')
        args = {'iduser_site': user_id}
        return self.adapter.write(create_cart_uri, args, post_process=self._post_process_write)

    def add_cart_product(self, cart_id, product_id):
        cart_items = self.list_cart(cart_id)
        matching_cart_entries = [p for p in cart_items if p['product_id'] == product_id]
        if matching_cart_entries:
            quantity = 1 + matching_cart_entries[0]['quantity']
        else:
            quantity = 1
        return self.update_cart_product(cart_id, product_id, quantity)

    def update_cart_product(self, cart_id, product_id, quantity):
        # TODO: set inactiv = 'D' for deleted products
        create_cart_entry_uri = self.adapter.uri_for('create_cart_entry')
        args = {'pid': self._existing_cart_item_id(cart_id, product_id) or 0,  # 0 for new
                'idparinte': cart_id,
                'idprodus': product_id,
                'cantitate': quantity}
        return self.adapter.write(create_cart_entry_uri, args)

    def _existing_cart_item_id(self, cart_id, product_id):
        cart_items = self.list_cart(cart_id)
        matching_cart_entries = [p for p in cart_items if p['product_id'] == product_id]
        if matching_cart_entries:
            return matching_cart_entries[0]
        else:
            return None

    def list_cart(self, cart_id):
        def post_process(data):
            cart_items = []
            json_root = 'cart_site_items'
            for item in data[json_root]:
                cart_item = {'cart_item_id': item['pidm'],
                             'product_id': item['zidprodus'],
                             'quantity': item['zcantitate'],
                             'price': item['zpret']}
                cart_items.append(cart_item)
            return cart_items

        list_cart_uri = self.adapter.uri_for('list_cart')
        return self.adapter.read(list_cart_uri, post_process=post_process, cache_timeout=TIMEOUT_NO_CACHE)
