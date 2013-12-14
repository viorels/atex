import xlsxwriter
from django.core.management.base import NoArgsCommand
from django.utils.text import slugify

from atexpc.atex_web.ancora_api import AncoraAPI
from atexpc.atex_web.models import Product
from atexpc.atex_web.dropbox_media import DropboxMedia

class Command(NoArgsCommand):
    def handle_noargs(self, *args, **options):
        api = AncoraAPI(api_timeout=300)  # 5 minutes
        for root_category in api.categories.get_main():
            print "root %s" % root_category
            subcategories = [c for c in api.categories.get_all()
                             if root_category['id'] == api.categories.get_main_category_for(root_category['id'])
                                and c['count'] > 0]
            self.write_xls(root_category, subcategories)

    def write_xls(self, root_category, subcategories):
        fname = "%s-%s.xlsx" % (root_category['code'], slugify(root_category['name']))
        workbook = xlsxwriter.Workbook(fname)
        for subcat in subcategories:
            worksheet_name = "%s-%s" % (subcat['code'], slugify(subcat['name']))
            worksheet_short_name = worksheet_name[:31]
            worksheet = workbook.add_worksheet(worksheet_short_name)
            products = self.products(subcat)
        workbook.close()

    def products(self, category):
        products = []
        for p in Product.objects.filter(category_id=category['id']):
            product = {'model': p.model}
            for spec in p.specs_list():
#                import pdb; pdb.set_trace()
                product[spec] = p.get_spec(spec)
            products.append(product)
        return products
