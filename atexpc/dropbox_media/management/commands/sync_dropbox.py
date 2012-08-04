from django.core.management.base import NoArgsCommand
from dropbox import session, client
from atexpc.dropbox_media.settings import (CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TYPE,
										   ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

class Command(NoArgsCommand):

    def handle_noargs(self, *args, **options):
		sess = session.DropboxSession(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TYPE)
		sess.set_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
		dropbox_client = client.DropboxClient(sess)

		delta = dropbox_client.delta()
		print "%d entries" % len(delta['entries'])
		for entry in delta['entries']:
		    path, meta = entry
		    print path

