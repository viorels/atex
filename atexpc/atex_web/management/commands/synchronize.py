import os
from functools import partial
from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.contrib.sites.models import get_current_site
from django.conf import settings
from atexpc.atex_web.models import Product, Categories

import logging
logger = logging.getLogger(__name__)

PRODUCT_DB_FIELDS = ('id', 'model', 'name')
SHOPMANIA_FEED_FILENAME = os.path.join(settings.PROJECT_ROOT,
    'atex_web', 'media', 'shopmania.csv')

class Command(BaseCommand):
    helf = "Synchronize Ancora products to local database AND (optionally) to Shopmania feed file"
    option_list = BaseCommand.option_list + (
        make_option('--to-shopmania',
            action='store_true',
            dest='shopmania',
            default=False,
            help='Also generate Shopmania data feed'),
        )

    def handle(self, *args, **options):
        writers = [self.create_or_update_products]

        if options['shopmania']:
            temp_feed_filename = SHOPMANIA_FEED_FILENAME + '.tmp'
            if os.path.exists(temp_feed_filename):
                os.remove(temp_feed_filename)
            writers.append(partial(self.add_products_to_shopmania_feed, temp_feed_filename))

        self.synchronize(writers)

        if options['shopmania']:
            if os.path.exists(temp_feed_filename) and os.path.exists(SHOPMANIA_FEED_FILENAME):
                os.remove(SHOPMANIA_FEED_FILENAME)
                os.rename(temp_feed_filename, SHOPMANIA_FEED_FILENAME)

        # Assign existing images for new products
        Product.objects.assign_images()

    def synchronize(self, writers):
        self.categories = Categories()
        for products_dict in self.fetch_products():
            for writer in writers:
                writer(products_dict)

    def fetch_products(self):
        for category in self.categories.get_all():
            category_id = category['id']
            logger.debug("Category %(name)s (%(count)d)", category)
            if category['count'] > 0:
                products = Product.objects.get_products(
                    category_id=category_id, keywords=None,
                    start=None, stop=None).get('products')
                products_dict = dict((int(p['id']), p) for p in products)
                yield products_dict

    def _model_product_dict(self, product):
        model_dict = {}
        for field in PRODUCT_DB_FIELDS:
            if field == 'id':
                model_dict[field] = int(product.get(field))
            else:
                model_dict[field] = product.get(field)
        return model_dict

    # Database

    def create_or_update_products(self, products):
        existing_products = Product.objects.in_bulk(products.keys())
        for product_id, new_product in products.items():
            old_product = existing_products.get(product_id)
            if old_product:
                new_product_fields = self._model_product_dict(new_product)
                updated_product = self._updated_product(old_product, new_product_fields)
                if updated_product:
                    logger.debug("Update %s", updated_product)
                    updated_product.save()

        insert_ids = set(products) - set(existing_products)
        if insert_ids:
            insert_list = [Product(**products[i]) for i in insert_ids]
            logger.debug("Insert %s", insert_list)
            Product.objects.bulk_create(insert_list)

    def _updated_product(self, product, product_update_dict):
        """ Returns updated product if the dict contains new data,
            otherwise returns None"""
        updated = False
        for field, new_value in product_update_dict.items():
            if new_value != getattr(product, field):
                setattr(product, field, new_value)
                updated = True
        return product if updated else None

    # Shopmania

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

    def _product_info(self, product):
        info = product.copy()
        info['category_path']  = self._get_category_path(product)
        info['description'] = '' # TODO: import description
        info['url'] = self._product_url(product)
        info['image_url'] = self._image_url(product)
        info['currency'] = 'RON'
        info['transport_cost'] = ''
        info['stock_info'] = self._translate_stock(product)
        info['gtin'] = ''
        return info

    def _translate_stock(self, product):
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
        category = self.categories.get_category_by_code(category_code)
        while category is not None:
            path.insert(0, category['name'])
            category = self.categories.get_parent_category(category['id'])
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





