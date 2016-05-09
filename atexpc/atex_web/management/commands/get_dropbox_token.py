from django.core.management.base import NoArgsCommand
from .dropbox_media import DropboxMedia

class Command(NoArgsCommand):
    def handle_noargs(self, *args, **options):
        session = DropboxMedia().session
        request_token = session.obtain_request_token()

        url = session.build_authorize_url(request_token)
        self.stdout.write("Url: %s\n" % url)
        self.stdout.write("Please visit this website and press the 'Allow' button, then hit 'Enter' here.\n")
        raw_input()
        
        # This will fail if the user didn't visit the above URL and hit 'Allow'
        access_token = session.obtain_access_token(request_token)

        self.stdout.write("DROPBOX_ACCESS_TOKEN = '%s'\n" % access_token.key)
        self.stdout.write("DROPBOX_ACCESS_TOKEN_SECRET = '%s'\n" % access_token.secret)
