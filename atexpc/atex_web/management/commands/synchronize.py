from base64 import b64encode
import os
from functools import partial
from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from django.utils.text import slugify
from django.contrib.sites.models import get_current_site
from django.conf import settings
from atexpc.atex_web.models import Product, Category
from atexpc.atex_web.ancora_api import AncoraAPI
from atexpc.atex_web.scrape import scrape_specs

import logging
logger = logging.getLogger(__name__)


class atomic_write(object):
    def __init__(self, name):
        self.fname = name
        self.temp_fname = name + '.tmp'

    def get_filename(self):
        return self.temp_fname

    def __enter__(self):
        if os.path.exists(self.temp_fname):
            os.remove(self.temp_fname)
        return self.temp_fname

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            if os.path.exists(self.temp_fname):
                if os.path.exists(self.fname):
                    os.remove(self.fname)
                os.rename(self.temp_fname, self.fname)
        else:
            if os.path.exists(self.temp_fname):
                os.remove(self.temp_fname)

        return False    # propagate errors


class Command(BaseCommand):
    helf = "Synchronize Ancora products to local database AND (optionally) to Shopmania feed file"
    option_list = BaseCommand.option_list + (
        make_option('--to-shops',
            action='store_true',
            dest='shops',
            default=False,
            help='Also generate Shopmania data feed'),
        make_option('--from-pcgarage',
            action='store_true',
            dest='pcgarage',
            default=False,
            help='Get product details'),
        )

    def handle(self, *args, **options):
        products_status = {}
        writers = [self.create_or_update_products_with_status(products_status)]

        with atomic_write(os.path.join(settings.MEDIA_ROOT, settings.SHOPMANIA_FEED_FILE)) as shopmania_feed, \
             atomic_write(os.path.join(settings.MEDIA_ROOT, settings.ALLSHOPS_FEED_FILE)) as allshops_feed:

            if options['shops']:
                writers.append(partial(self.add_products_to_shopmania_feed, shopmania_feed))
                writers.append(partial(self.add_products_to_allshops_feed, allshops_feed))

            if options['pcgarage']:
                writers.append(self.get_and_save_specs)

            self.synchronize(writers)
            self.delete_products_other_then(products_status)

            # Assign existing images for new products
            Product.objects.assign_images()

    def synchronize(self, writers):
        self.api = AncoraAPI(api_timeout=300)  # 5 minutes
        self.synchronize_categories()
        for products_dict in self.fetch_products():
            for writer in writers:
                writer(products_dict)

    def fetch_products(self):
        for category in self.api.categories.get_all():
            category_id = category['id']
            logger.debug("Category %(name)s (%(count)d)", category)
            if category['count'] > 0:
                products = self.api.products.get_products(
                    category_id=category_id, keywords=None,
                    start=None, stop=None).get('products')
                products_dict = dict((int(p['id']), p) for p in products)
                for p in products_dict.values():     # augment products with category_id
                    p['category_id'] = category_id
                yield products_dict

    # Database

    def synchronize_categories(self):
        for category in self.api.categories.get_all():
            parent = self.api.categories.get_parent_category(category['id'])
            parent_id = parent['id'] if parent is not None else None
            try:
                category_store = Category.objects.get(id=category['id'])
                category_store.name = category['name']
                category_store.code = category['code']
                category_store.parent_id = parent_id
                category_store.save()
            except Category.DoesNotExist:
                Category.objects.create(id=category['id'],
                                        name=category['name'],
                                        code=category['code'],
                                        parent_id=parent_id)

    def create_or_update_products_with_status(self, products_status):
        def create_or_update_products(products):
            existing_products = Product.objects.in_bulk(products.keys())
            for product_id, new_product in products.items():
                products_status[product_id] = True

                old_product = existing_products.get(product_id)
                if old_product:
                    new_product_fields = Product.from_raw(new_product)
                    updated_product = old_product.updated_product(new_product_fields)
                    if updated_product:
                        logger.debug("Update %s", updated_product)
                        updated_product.save()

            insert_ids = set(products) - set(existing_products)
            if insert_ids:
                insert_list = [Product(raw=products[i]) for i in insert_ids]
                logger.debug("Insert %s", insert_list)
                Product.objects.bulk_create(insert_list)

        return create_or_update_products

    def delete_products_other_then(self, products):
        existing_products = [p['id'] for p in Product.objects.values('id')]
        delete_ids = set(existing_products) - set(products)
        if (float(len(delete_ids)) / len(existing_products)) < 0.33:
            logger.debug("Delete %s", delete_ids)
            for product_id in delete_ids:
                Product.objects.get(id=product_id).delete()

    # Shopping sites export

    def add_products_to_shopmania_feed(self, filename, products):
        feed_line_items = (
            'category_path', 'brand', 'model', 'id', 'name', 'description', 'url',
            'image_url', 'price', 'currency', 'transport_cost', 'stock_info', 'gtin')
        with open(filename, "a") as feed:
            for product in products.values():
                product_info = self._product_info(product)
                # TODO: is float(price) > 0 ?
                feed_line = '|'.join(self._clean(unicode(product_info.get(item, '')))
                                     for item in feed_line_items)
                feed.write(feed_line)
                feed.write('\n')

    def add_products_to_allshops_feed(self, filename, products):
        feed_line_items = (
            'category_id', 'category_name', 'name', 'model', 'description', 
            'image_url', 'kw1', 'kw2', 'kw3', 'brand', 'price_standard', 'price_discount',
            'currency_id', 'url', 'stock_allshops', 'sizes')
        with open(filename, "a") as feed:
            for product in products.values():
                product_info = self._product_info(product)
                # TODO: is float(price) > 0 ?
                feed_line = ';'.join('"%s"' % b64encode(self._clean(unicode(product_info.get(item, ''))))
                                     for item in feed_line_items)
                feed.write(feed_line)
                feed.write('\n')

    def _product_info(self, product):
        info = product.copy()

        info['category_path']  = self._get_category_path(product)
        info['description'] = self.api.products.get_product(info['id'])['description']
        info['url'] = self._product_url(product)
        info['image_url'] = self._image_url(product)
        info['currency'] = 'RON'
        info['transport_cost'] = ''
        info['stock_info'] = self._translate_stock_shopmania(product)
        info['gtin'] = ''

        # allshops
        info['category_name'] = self.api.categories.get_category_by_code(info['category_code'])['name']
        info['price_standard'] = info['price'] if not info['old_price'] else info['old_price']
        info['price_discount'] = info['price'] if info['old_price'] else ''
        info['currency_id'] = 1
        # all shops stock id is the same with atex status
        info['stock_allshops'] = info['stock_status']
        info['sizes'] = ''

        return info

    def _translate_stock_shopmania(self, product):
        shopmania_stock = {
            'stock': 'In stock / In stoc',
            'order': 'Available for order / Disponibil la comanda',
            'unavailable': 'Out of stock / Stoc epuizat',
            'preorder': 'Preorder / Disponibil cu precomanda'}

        stock_dict = {
            'Disponibil in stoc': shopmania_stock['stock'],
            'Order': shopmania_stock['order'],
            'Call': shopmania_stock['order']}

        return stock_dict.get(product['stock_info'], shopmania_stock['stock'])

    def _get_category_path(self, product):
        path = []
        category_code = product['category_code']
        category = self.api.categories.get_category_by_code(category_code)
        while category is not None:
            path.insert(0, category['name'])
            category = self.api.categories.get_parent_category(category['id'])
        return " > ".join(path)

    def _build_absolute_uri(self, relative_uri):
        return ''.join(['http://', get_current_site(None).domain, relative_uri])

    def _product_url(self, product):
        uri = reverse('product', kwargs={'product_id': product['id'],
                                         'slug': slugify(product['name'])})
        return self._build_absolute_uri(uri)

    def _image_url(self, product):
        images = Product(model=product['model']).images()
        if images and not images[0].is_not_available():
            return self._build_absolute_uri(images[0].image.url)
        else:
            return ''

    def _clean(self, field):
        if field is None:
            return None
        strip_chars = ('|', '\n', '\r')
        return reduce(lambda s, c: s.replace(c, ''), strip_chars, field)

    # Specifications

    def get_and_save_specs(self, products):
        for product_meta in products.values():
            product = Product.objects.get(id=product_meta['id'])
            existing_specs = product.specs.count()
            if not existing_specs:
                specs = scrape_specs(product_meta['model'])
                product.update_specs(specs)
