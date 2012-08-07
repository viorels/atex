from django.core.management.base import NoArgsCommand
from dropbox import rest, session
from django.conf import settings

class Command(NoArgsCommand):

    def handle_noargs(self, *args, **options):
        sess = session.DropboxSession(settings.DROPBOX_APP_KEY,
                                      settings.DROPBOX_APP_SECRET,
                                      settings.DROPBOX_ACCESS_TYPE)
        request_token = sess.obtain_request_token()

        url = sess.build_authorize_url(request_token)
        self.stdout.write("Url: %s\n" % url)
        self.stdout.write("Please visit this website and press the 'Allow' button, then hit 'Enter' here.\n")
        raw_input()
        
        # This will fail if the user didn't visit the above URL and hit 'Allow'
        access_token = sess.obtain_access_token(request_token)

        self.stdout.write("DROPBOX_ACCESS_TOKEN = '%s'\n" % access_token.key)
        self.stdout.write("DROPBOX_ACCESS_TOKEN_SECRET = '%s'\n" % access_token.secret)
