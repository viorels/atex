from django.core.management.base import BaseCommand
from atexpc.atex_web.models import Product
from atexpc.atex_web.dropbox_media import DropboxMedia
from pid import PidFile

class Command(BaseCommand):
    def handle(self, *args, **options):
        with PidFile(force_tmpdir=True):
            DropboxMedia().synchronize()
            Product.objects.assign_images()
