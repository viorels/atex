import xlsxwriter
from django.core.management.base import NoArgsCommand
from django.db.models import Count
from django.utils.text import slugify

from atexpc.atex_web.ancora_api import AncoraAPI
from atexpc.atex_web.models import Product, ProductSpecification
from atexpc.atex_web.dropbox_media import DropboxMedia

MODEL_COL = 'Model'
IGNORE_COLS = ['Cod producator']


class Command(NoArgsCommand):
    def handle_noargs(self, *args, **options):
        api = AncoraAPI(api_timeout=300)  # 5 minutes
        for root_category in api.categories.get_main():
            print "root %s" % root_category['name']
            subcategories = [c for c in api.categories.get_all()
                             if root_category['id'] == api.categories.get_main_category_for(c['id'])
                                and c['count'] > 0]
            self.write_xls(root_category, subcategories)

    def write_xls(self, root_category, subcategories):
        fname = "%s-%s.xlsx" % (root_category['code'], slugify(root_category['name']))
        workbook = xlsxwriter.Workbook(fname)
        for subcat in subcategories:
            products = self.products(subcat)
            if products:
                worksheet_name = "%s-%s" % (subcat['code'], slugify(subcat['name']))
                worksheet_short_name = worksheet_name[:31]
                worksheet = workbook.add_worksheet(worksheet_short_name)
                headers = self.xls_columns(products)
                bold = workbook.add_format({'bold': 1})
                worksheet.set_column(0, 0, 15)
                self.write_row(worksheet, 0, headers, bold)
                for row_number, product in enumerate(products):
                    product_cols = [product.get(col, '') for col in headers]
                    self.write_row(worksheet, row_number + 1, product_cols)
        workbook.close()

    def write_row(self, worksheet, row_number, items, format=None):
        for i, item in enumerate(items):
            worksheet.write(row_number, i, item, format)

    def products(self, category):
        products = []
        for p in (Product.objects
                         .annotate(specs_count=Count('specs'))
                         .filter(category_id=category['id'], specs_count__gt=0)):
            product = {MODEL_COL: p.model}
            prod_specs = ProductSpecification.objects.filter(product=p)
            for spec in prod_specs:
                spec_name = "%s|%s" % (spec.spec.group.name, spec.spec.name) if spec.spec.group.name else spec.spec.name
                if spec_name not in IGNORE_COLS:
                    product[spec_name] = spec.value
            products.append(product)
        return products

    def xls_columns(self, products):
        columns = set(spec for product in products for spec in product.keys())
        return sorted(columns, key=self.columns_sort_key)

    def columns_sort_key(self, column):
        if column == MODEL_COL:
            column_type = 0
        elif '|' not in column:
            column_type = 1
        else:
            column_type = 2
#            column = '|'.join(reversed(column.split('|'))) # spec group first
        return (column_type, column)
