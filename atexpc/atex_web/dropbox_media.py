import os
import re
import shutil
import time

from django.conf import settings
from django.core.files import File, temp
from dropbox import rest, session, client
from dropbox.rest import RESTSocketError

from atexpc.atex_web.models import Dropbox, Product, Image, StorageWithOverwrite

import logging
logger = logging.getLogger(__name__)


class DropboxMedia(object):
    products_path = "/Atex-media/products"
    products_path_re = r"/products/(?P<folder>[^/]+)/(?P<resource>[^/]+)(?P<other>/.*)?"
    max_path_length = 128 # TODO: introspect model
    local_dropbox_path = os.path.join(os.path.expanduser("~"), 'Dropbox')

    def __init__(self, use_local_dropbox=False, *args, **kwargs):
        super(DropboxMedia, self).__init__(*args, **kwargs)
        self.use_local_dropbox = use_local_dropbox # relevant for reading
        self.session = self._get_session()
        if settings.DROPBOX_ACCESS_TOKEN and settings.DROPBOX_ACCESS_TOKEN_SECRET:
            self._dropbox = self._get_client()

    def _get_session(self):
        return session.DropboxSession(settings.DROPBOX_APP_KEY,
                                      settings.DROPBOX_APP_SECRET,
                                      settings.DROPBOX_ACCESS_TYPE)

    def _get_client(self):
        self.session.set_token(settings.DROPBOX_ACCESS_TOKEN,
                               settings.DROPBOX_ACCESS_TOKEN_SECRET)
        return client.DropboxClient(self.session)

    def _delta_cursor(self, new_cursor=None):
        state, created = Dropbox.objects.get_or_create(app_key=settings.DROPBOX_APP_KEY)
        if new_cursor is not None:
            logger.debug("Saving cursor: %s", new_cursor)
            state.delta_cursor = new_cursor
            state.save()
        return state.delta_cursor

    def create_product_folder(self, name):
        path = os.path.join(self.products_path, name)
        try:
            self._dropbox.file_create_folder(path)
        except rest.ErrorResponse, e:
            logger.error(e)

    def synchronize(self): # TODO: handle rate limit (503 errors)
        last_cursor = self._delta_cursor()
        has_more = True
        while has_more:
            delta = self._dropbox.delta(last_cursor)
            has_more = delta['has_more']
            for entry in delta['entries']:
                path, meta = entry
                path_match = re.search(self.products_path_re, path, re.IGNORECASE)
                if not path_match:
                    continue
                if len(path) > self.max_path_length:
                    logger.error("Error: path too long (%d): %s", len(path), path)
                    continue
                if meta:
                    path_with_case = meta['path']
                    if not meta['is_dir'] and path_match.group('resource'):
                        if not path_match.group('other') and path.endswith(Product.image_extensions):
                            self._copy_file(path_with_case, meta, self._storage_image_writer)
                        elif (path_match.group('resource').endswith(Product.html_extensions)
                              or path_match.group('other')):
                            self._copy_file(path_with_case, meta, self._storage_file_writer)
                else:
                    meta = self._dropbox.metadata(path, include_deleted=True)
                    if not meta['is_dir']:
                        path_with_case = meta['path']
                        self._delete_file(path_with_case)

            last_cursor = delta['cursor']
            self._delta_cursor(last_cursor)
            logger.debug("Cursor: %s", last_cursor)
            

    def _relative_path(self, path):
        return path[1:] if path[0] == '/' else path

    def _copy_file(self, path, meta, writer):
        logger.debug("Uploading %s", path)

        if self.use_local_dropbox:
            self._local_file_reader(self._relative_path(path), meta, writer)
        else:
            self._dropbox_file_reader(self._relative_path(path), meta, writer)

    def _local_file_reader(self, path, meta, writer):
        file_path = os.path.join(self.local_dropbox_path, path)
        with open(file_path) as f:
            writer(path, f)

    def _dropbox_file_reader(self, path, meta, writer):
        rev = meta['rev']

        attempts = 0
        dropbox_file = None
        while attempts < 3 and not dropbox_file:
            try:
                dropbox_file = self._dropbox.get_file(path, rev)
            except RESTSocketError, e:
                attempts += 1
                logger.debug(e)
                time.sleep(3)
        if not dropbox_file:
            return

        chunk_size = 1024 ** 2
        with temp.NamedTemporaryFile(delete=False) as tempfile:
            shutil.copyfileobj(dropbox_file, tempfile)

        with open(tempfile.name) as f:
            writer(path, f)
        os.unlink(tempfile.name)

    def _storage_image_writer(self, path, f):
        image, created = Image.objects.get_or_create(path=path)
        django_file = File(f)
        image.image.save(path, django_file)

    def _storage_file_writer(self, path, f):
        media_path = Image()._media_path(path)
        django_file = File(f)
        StorageWithOverwrite().save(media_path, django_file)

    def _delete_file(self, path):
        logger.debug("Deleting %s", path)

        # cleanup database image with this name, if any
        try:
            image = Image.objects.get(path=self._relative_path(path))
            image.delete()
        except Image.DoesNotExist, e:
            pass

        # delete storage file with this name
        media_path = Image()._media_path(path)
        StorageWithOverwrite().delete(media_path)
