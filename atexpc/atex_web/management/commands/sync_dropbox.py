from django.core.management.base import NoArgsCommand
from atexpc.atex_web.models import Product
from atexpc.atex_web.dropbox_media import DropboxMedia

class Command(NoArgsCommand):
    def handle_noargs(self, *args, **options):
        DropboxMedia().synchronize()
        Product.objects.assign_images()
