import csv

from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.contrib.redirects.models import Redirect

from atexpc.atex_web.models import Product
from atexpc.atex_web.ancora_api import AncoraAPI


class Command(BaseCommand):
    def handle(self, *args, **options):
        if args:
            product_file_name = args[0]
            self.generate_products(product_file_name)
        else:
            print "I need a csv file with old_id, product_code as argument"
        #self.generate_categories()

    def generate_products(self, product_file_name):
        with open(product_file_name, 'rb') as product_file:
            old_product_csv = csv.reader(product_file)
            for i, model in old_product_csv:
                try:
                    new_product = Product.objects.get(model__iexact=model)
                except Product.MultipleObjectsReturned as e:
                    new_product = Product.objects.get(model=model)
                except Product.DoesNotExist as e:
                    new_product = None
                if new_product:
                    old_path = "/Detalii.aspx?IdProdus=%s" % i
                    new_path = reverse('product', kwargs={'product_id': new_product.id,
                                      'slug': slugify(new_product.name)})
                    print "%s -> %s" % (old_path, new_path)
                    Redirect.objects.get_or_create(site_id=1, old_path=old_path, new_path=new_path)

    def generate_categories(self):
        categories = AncoraAPI().categories.get_all()
        new_categories = dict((c['name'].lower(), c['id']) for c in categories)
        with open('category.csv', 'rb') as category_file:
            old_category_csv = csv.reader(category_file)
            for i, name in old_category_csv:
                print ', '.join([i, name, new_categories.get(name.lower(), 'NA')])