from django.core.management.base import NoArgsCommand
from atexpc.atex_web.models import Product
from atexpc.atex_web.dropbox_media import DropboxMedia
from pid import PidFile

class Command(NoArgsCommand):
    def handle_noargs(self, *args, **options):
        with PidFile(force_tmpdir=True):
            DropboxMedia().remove_unused_images()
