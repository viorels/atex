from django.core.management.base import NoArgsCommand
from atexpc.atex_web.models import DropboxMedia

class Command(NoArgsCommand):
    def handle_noargs(self, *args, **options):
        DropboxMedia().synchronize()
