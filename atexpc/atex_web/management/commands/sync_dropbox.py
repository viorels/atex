import os
from django.core.files import temp as tempfile

from django.core.management.base import NoArgsCommand
from django.core.files import File
from django.conf import settings
from dropbox import session, client
from atexpc.atex_web.models import Image

USE_LOCAL_DROPBOX = False # relevant for reading

class Command(NoArgsCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        sess = session.DropboxSession(settings.DROPBOX_APP_KEY,
                                      settings.DROPBOX_APP_SECRET,
                                      settings.DROPBOX_ACCESS_TYPE)
        sess.set_token(settings.DROPBOX_ACCESS_TOKEN,
                       settings.DROPBOX_ACCESS_TOKEN_SECRET)
        self._dropbox = client.DropboxClient(sess)

        if USE_LOCAL_DROPBOX:
            self._media_cache = self._list_local_media_files()

    def handle_noargs(self, *args, **options):

        delta = self._dropbox.delta()
        for entry in delta['entries'][0:2]:
            path, meta = entry
            # if new file
            self._copy_file(path, meta, self._s3_file_writer)

        self.stdout.write("%d entries\n" % len(delta['entries']))

    def _list_local_media_files(self):
        pass

    def _copy_file(self, path, meta, writer):
        self.stdout.write("Uploading %s: %s\n" % (path, meta))

        relative_path = path[1:] if path[0] == '/' else path 
        if USE_LOCAL_DROPBOX:
            self._local_file_reader(relative_path, meta, writer)
        else:
            self._dropbox_file_reader(relative_path, meta, writer)

    def _local_file_reader(self, path, meta, writer):
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        with open(file_path) as f:
            writer(path, f)

    def _dropbox_file_reader(self, path, meta, writer):
        dropbox_file = self._dropbox.get_file(path)

        chunk_size = 1024 ** 2
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            for chunk in dropbox_file.read(chunk_size):
                temp.write(chunk)

        with open(temp.name) as f:
            writer(path, f)
        os.unlink(temp.name)

    def _s3_file_writer(self, path, f):
        path_lower = path.lower()
        image, created = Image.objects.get_or_create(path=path_lower)
        django_file = File(f)
        image.image.save(path_lower, django_file)
