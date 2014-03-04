import string
from operator import itemgetter

from django.conf import settings
from django.contrib.auth import get_user_model

from atexpc.ancora_api.api import Ancora, AncoraAdapter


class AncoraAPI(object):
    def __init__(self, adapter_class=AncoraAdapter,
                       base_uri=settings.ANCORA_URI,
                       use_backend=None, api_timeout=None):
        adapter_args = {'base_uri': settings.ANCORA_URI}
        if use_backend is not None:
            adapter_args['use_backend'] = use_backend
        if api_timeout is not None:
            adapter_args['api_timeout'] = api_timeout
        self._ancora = Ancora(adapter=adapter_class(**adapter_args))
        self.categories = CategoriesAPI(api=self._ancora)
        self.products = ProductsAPI(api=self._ancora, categories=self.categories)
        self.users = UsersAPI(api=self._ancora)
        self.cart = CartAPI(api=self._ancora)


class BaseAPI(object):
    """Base class for APIs"""
    def __init__(self, api):
        super(BaseAPI, self).__init__()
        self._api = api


class CategoriesAPI(BaseAPI):
    def get_all(self):
        if not hasattr(self, '_categories'):
            categories = self._api.categories()
            # skip categories with code that begin with letters,
            # e.g. "diverse" with code "XX"
            self._categories = [category for category in categories
                                if category['code'].startswith(tuple(string.digits))]
        return self._categories

    def get_main(self):
        return self.get_children(parent=None)

    def get_children(self, parent=None):
        """Return child categories for the specified category
           or top categories if None specified"""
        categories = [c for c in self.get_all() if c['parent'] == parent]
        return categories

    def get_category(self, category_id):
        if category_id is None:
            return None
        all_categories = self.get_all()
        categories = [c for c in all_categories if c['id'] == category_id]
        if len(categories) == 1:
            return categories[0]
        else:
            return None

    def get_category_by_code(self, category_code):
        if category_code is None:
            return None
        all_categories = self.get_all()
        categories = [c for c in all_categories if c['code'] == category_code]
        if len(categories) == 1:
            return categories[0]
        else:
            return None

    def get_parent_category(self, category_id):
        if category_id is None:
            return None
        category = self.get_category(category_id)
        category_code_parts = category['code'].split('.')
        parent_category_code_parts = category_code_parts[:-1]
        if parent_category_code_parts:
            parent_category_code = '.'.join(parent_category_code_parts)
            parent_categories = [c for c in self.get_all() if c['code'] == parent_category_code]
            if len(parent_categories) == 1:
                parent_category = parent_categories[0]
            else:
                parent_category = None
        else:
            parent_category = None
        return parent_category

    def get_main_category_for(self, category_id):
        """Returns the id of the top category that the argument belongs to"""
        category = self.get_category(category_id)
        parent_category_code = category['code'].split('.')[0]
        return [c for c in self.get_all() if c['code'] == parent_category_code][0]['id']

    def get_selectors(self, category_id, selectors_active, price_min, price_max, stock):
        if not hasattr(self, '_selectors'):
            self._selectors = self._api.selectors(
                category_id, selectors_active,
                price_min=price_min, price_max=price_max, stock=stock)
        return self._selectors


class ProductsAPI(BaseAPI):
    def __init__(self, categories, *args, **kwargs):
        super(ProductsAPI, self).__init__(*args, **kwargs)
        self.categories = categories

    def get_product(self, product_id):
        product = self._api.product(product_id)
        if product is not None:
            category = self.categories.get_category_by_code(product['category_code'])
            if category:
                product['category_id'] = category['id']
            else:
               # the product is invalid if the category code is unknown (e.g. XX)
               product = None
        return product

    def get_and_store(self, product_id, product_storer):
        """Fetch product from API and store it using the specified callable"""
        product_raw = self.get_product(product_id)
        if product_raw is None:
            return None
        product = product_storer(product_raw, update=True)
        product.raw = product_raw
        return product

    def get_product_list(self, product_ids):
        return self._api.product_list(product_ids).get('products')

    def get_products(self, *args, **kwargs):
        return self._api.search_products(*args, **kwargs)

    def get_products_with_hits(self, category_id, keywords, selectors,
                     price_min, price_max, stock, start, stop,
                     augmenter_with_hits, **kwargs):
        products_info = self.get_products(
            category_id=category_id, keywords=keywords, selectors=selectors,
            price_min=price_min, price_max=price_max, stock=stock)
        products = augmenter_with_hits(products_info.get('products'))
        products.sort(key=itemgetter('hits'), reverse=True)
        return {'products': products[start:stop],
                'total_count': products_info['total_count']}

    def get_recommended(self, limit):
        return self._api.products_recommended(limit).get('products')

    def get_promotional(self, limit):
        return self._api.products_promotional(limit).get('products')

    def get_brands(self):
        return self._api.brands()


class UsersAPI(BaseAPI):
    def create_user(self, **kwargs):
        return self._api.create_user(**kwargs)

    def get_user(self, email):
        return self._api.get_user(email)

    def create_or_update_user(self, **kwargs):
        email = kwargs.get('email')
        user = self.get_user(email)
        if user is not None:
            # TODO: update user
            return user['id']
        else:
            user_id = self.create_user(**kwargs)
            return user_id

    def get_users(self):
        return self._api.get_users()


class CartAPI(BaseAPI):
    def get_cart(self, cart_id):
        """ Ancora does't tell if the cart exists so we assume it does"""
        return cart_id

    def create_cart(self, user_id):
        return self._api.create_cart(user_id)

    def list_cart(self, cart_id):
        return self._api.list_cart(cart_id)

    def get_cart_price(self, cart_id, delivery=False, payment='cash'):
        return self._api.get_cart_price(cart_id, delivery, payment)

    def add_product(self, cart_id, product_id):
        return self._api.add_cart_product(cart_id, product_id)

    def remove_product(self, cart_id, product_id):
        return self._api.remove_cart_product(cart_id, product_id)

    def update_product(self, cart_id, product_id, count):
        return self._api.update_cart_product(cart_id, product_id, count)

    def get_customers(self, user_id):
        return self._api.get_customers(user_id)

    def get_addresses(self, user_id):
        return self._api.get_addresses(user_id)

    def create_order(self, **kwargs):
        return self._api.create_order(**kwargs)
