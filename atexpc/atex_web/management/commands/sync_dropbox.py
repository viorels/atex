from django.core.management.base import NoArgsCommand
from atexpc.atex_web.models import DropboxMedia, Product

class Command(NoArgsCommand):
    def handle_noargs(self, *args, **options):
        DropboxMedia().synchronize()
        Product.objects.assign_images()
