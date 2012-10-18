import os
import re
import shutil

from django.core.files import temp as tempfile
from django.core.management.base import NoArgsCommand
from django.core.files import File
from django.core.files.storage import default_storage
from django.conf import settings

from dropbox import session, client
from atexpc.atex_web.models import Dropbox, Image

PRODUCTS_PATH = r"/products/(?P<folder>[^/]+)/(?P<resource>[^/]+)(?P<other>/.*)?"
USE_LOCAL_DROPBOX = False # relevant for reading
LOCAL_DROPBOX_PATH = os.path.join(os.environ.get('HOME'), 'Dropbox')
MAX_PATH_LENGTH = 128 # TODO: introspect model
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
HTML_EXTENSIONS = ('.html', '.htm')

class Command(NoArgsCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        sess = session.DropboxSession(settings.DROPBOX_APP_KEY,
                                      settings.DROPBOX_APP_SECRET,
                                      settings.DROPBOX_ACCESS_TYPE)
        sess.set_token(settings.DROPBOX_ACCESS_TOKEN,
                       settings.DROPBOX_ACCESS_TOKEN_SECRET)
        self._dropbox = client.DropboxClient(sess)

    def handle_noargs(self, *args, **options):
        dropbox_state, __ = Dropbox.objects.get_or_create(app_key=settings.DROPBOX_APP_KEY)
        cursor = dropbox_state.delta_cursor
        has_more = True
        while has_more:
            delta = self._dropbox.delta(cursor)
            has_more = delta['has_more']
            cursor = delta['cursor']
            for entry in delta['entries']:
                path, meta = entry
                path_match = re.search(PRODUCTS_PATH, path, re.IGNORECASE)
                if not path_match:
                    continue
                if len(path) > MAX_PATH_LENGTH:
                    self.stderr.write("Error: path too long (%d): %s\n"
                                      % (len(path), path))
                    continue
                if meta:
                    path_with_case = meta['path']
                    if not meta['is_dir'] and path_match.group('resource'):
                        if not path_match.group('other') and path.endswith(IMAGE_EXTENSIONS):
                            self._copy_file(path_with_case, meta, self._storage_image_writer)
                        elif (path_match.group('resource').endswith(HTML_EXTENSIONS)
                              or path_match.group('other')):
                            self._copy_file(path_with_case, meta, self._storage_file_writer)
                else:
                    meta = self._dropbox.metadata(path, include_deleted=True)
                    if not meta['is_dir']:
                        path_with_case = meta['path']
                        self._delete_file(path_with_case)

            self.stdout.write("Cursor: %s\n" % cursor)
            dropbox_state.delta_cursor = cursor
            dropbox_state.save()

    def _relative_path(self, path):
        return path[1:] if path[0] == '/' else path

    def _copy_file(self, path, meta, writer):
        self.stdout.write("Uploading %s: %s\n" % (path, 'meta'))

        if USE_LOCAL_DROPBOX:
            self._local_file_reader(self._relative_path(path), meta, writer)
        else:
            self._dropbox_file_reader(self._relative_path(path), meta, writer)

    def _local_file_reader(self, path, meta, writer):
        file_path = os.path.join(LOCAL_DROPBOX_PATH, path)
        with open(file_path) as f:
            writer(path, f)

    def _dropbox_file_reader(self, path, meta, writer):
        rev = meta['rev']
        dropbox_file = self._dropbox.get_file(path, rev)

        chunk_size = 1024 ** 2
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            shutil.copyfileobj(dropbox_file, temp)

        with open(temp.name) as f:
            writer(path, f)
        os.unlink(temp.name)

    def _storage_image_writer(self, path, f):
        image, created = Image.objects.get_or_create(path=path)
        django_file = File(f)
        image.image.save(path, django_file)

    def _storage_file_writer(self, path, f):
        media_path = Image()._media_path(path)
        django_file = File(f)
        default_storage.save(media_path, django_file)

    def _delete_file(self, path):
        self.stdout.write("Deleting %s\n" % (path,))

        # cleanup database image with this name, if any
        try:
            image = Image.objects.get(path=self._relative_path(path))
            image.delete()
        except Image.DoesNotExist, e:
            pass

        # delete storage file with this name
        media_path = Image()._media_path(path)
        default_storage.delete(media_path)
