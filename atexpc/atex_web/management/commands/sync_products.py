from django.core.management.base import NoArgsCommand
from atexpc.atex_web.models import Product, Categories

import logging
logger = logging.getLogger(__name__)


class Command(NoArgsCommand):
    update_fields = ('id', 'model', 'name')

    def _model_product_dict(self, product):
        model_dict = {}
        for field in self.update_fields:
            if field == 'id':
                model_dict[field] = int(product.get(field))
            else:
                model_dict[field] = product.get(field)
        return model_dict

    def _updated_product(self, product, product_update_dict):
        """ Returns updated product if the dict contains new data,
            otherwise returns None"""
        updated = False
        for field, new_value in product_update_dict.items():
            if new_value != getattr(product, field):
                setattr(product, field, new_value)
                updated = True
        return product if updated else None

    def _create_or_update_products(self, products):
        existing_products = Product.objects.in_bulk(products.keys())
        for product_id, new_product in products.items():
            old_product = existing_products.get(product_id)
            if old_product:
                updated_product = self._updated_product(old_product, new_product)
                if updated_product:
                    logger.debug("Update %s", updated_product)
                    updated_product.save()

        insert_ids = products.viewkeys() - existing_products.viewkeys()
        if insert_ids:
            insert_list = [Product(**products[i]) for i in insert_ids]
            logger.debug("Insert %s", insert_list)
            Product.objects.bulk_create(insert_list)

    def handle_noargs(self, *args, **options):
        categories = Categories().get_all()
        for category in categories:
            category_id = category['id']
            logger.debug("Category %(name)s (%(count)d)", category)
            if category['count'] > 0:
                products = Product.objects.get_products(
                    category_id=category_id, keywords=None,
                    start=None, stop=None).get('products')
                products_dict = dict((int(p['id']), self._model_product_dict(p))
                                     for p in products)
                self._create_or_update_products(products_dict)

        # Assign existing images for new products
        Product.objects.assign_images()
