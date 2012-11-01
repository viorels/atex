from django.core.management.base import NoArgsCommand
from atexpc.atex_web.models import Product, Categories

import logging
logger = logging.getLogger(__name__)

# http://www.preetk.com/node/optimizing-mass-commits-django-django_bulk_save/
# http://people.iola.dk/olau/python/bulkops.py

class Command(NoArgsCommand):
    excluded_fields = ['updated', 'has_folder']
    update_fields = [f.name for f in Product._meta.fields if f.name not in excluded_fields]

    def _model_product_dict(self, product, category_id):
        model_dict = {}
        for field in self.update_fields:
            if field == 'id':
                model_dict[field] = int(product.get(field))
            else:
                model_dict[field] = product.get(field)
        model_dict['category_id'] = int(category_id)
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
        insert_list = [Product(**products[i]) for i in insert_ids]
        logger.debug("Insert %s", insert_list)
        Product.objects.bulk_create(insert_list)

        delete_ids = existing_products.viewkeys() - products.viewkeys()
        delete_list = [existing_products.get(i) for i in delete_ids]
        logger.debug("Delete %s", delete_list)
        for old_product in delete_list:
            old_product.delete()

    def handle_noargs(self, *args, **options):
        categories = Categories().get_all()
        # TODO: delete old categories
        for category in categories:
            category_id = category['id']
            logger.debug("Category %(name)s (%(count)d)", category)
            if category['count'] > 0:
                products = Product.objects.get_products(
                    category_id=category_id, keywords=None,
                    start=None, stop=None).get('products')
                products_dict = dict((int(p['id']), self._model_product_dict(p, category_id))
                                     for p in products)
                self._create_or_update_products(products_dict)

        # Assign existing images for new products
        Product.objects.assign_images()
