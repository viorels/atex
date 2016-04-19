from hashlib import sha256
import hmac
import os
import re
import shutil
import time

from django.conf import settings
from django.core.files import File, temp
import dropbox
from dropbox.files import FileMetadata, FolderMetadata, DeletedMetadata
from dropbox.exceptions import ApiError

from atexpc.atex_web.models import Dropbox, Product, Image, StorageWithOverwrite, _media_path

import logging
logger = logging.getLogger(__name__)


class DropboxMedia(object):
    products_path = "/Atex-media/products"
    products_path_re = r"/products/(?P<folder>[^/]+)/(?P<resource>[^/]+)(?P<other>/.*)?"
    max_path_length = 128 # TODO: introspect model

    def __init__(self, *args, **kwargs):
        super(DropboxMedia, self).__init__(*args, **kwargs)
        if settings.DROPBOX_ACCESS_TOKEN_V2:
            self._dropbox = dropbox.Dropbox(settings.DROPBOX_ACCESS_TOKEN_V2)

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
            self._dropbox.files_create_folder(path)
        except ApiError, e:
            logger.error(e)

    def synchronize(self): # TODO: handle rate limit (503 errors)
        last_cursor = self._delta_cursor()
        has_more = True
        while has_more:
            if not last_cursor:
                delta = self._dropbox.files_list_folder(self.products_path, recursive=True)
            else:
                delta = self._dropbox.files_list_folder_continue(last_cursor)
            has_more = delta.has_more
            for entry in delta.entries:
                path = entry.path_display
                path_match = re.search(self.products_path_re, path, re.IGNORECASE)
                if not path_match:
                    continue
                if len(path) > self.max_path_length:
                    logger.error("Error: path too long (%d): %s", len(path), path)
                    continue
                if isinstance(entry, FileMetadata) and path_match.group('resource'):
                    if not path_match.group('other') and path.lower().endswith(Product.image_extensions):
                        self._copy_file(entry)
                    elif (path_match.group('resource').lower().endswith(Product.html_extensions)
                          or path_match.group('other')):
                        self._copy_file(entry)
                elif isinstance(entry, DeletedMetadata):
                    self._delete_file(path)

            last_cursor = delta.cursor
            self._delta_cursor(last_cursor)
            logger.debug("Cursor: %s", last_cursor)

    def validate_webhook_request(self, body, signature):
        """Validate that the request is properly signed by Dropbox.
           (If not, this is a spoofed webhook.)"""

        return signature == hmac.new(settings.DROPBOX_APP_SECRET, body, sha256).hexdigest()

    def get_account_id(self):
        return self._dropbox.users_get_current_account().account_id

    ### private methods ###

    def _relative_path(self, path):
        return path[1:] if path[0] == '/' else path

    def _copy_file(self, entry):
        logger.debug("Downloading %s", entry.path_display)

        with temp.NamedTemporaryFile(delete=False) as tempfile:
            tempfile_name = tempfile.name   # temp file is created and closed empty
        self._dropbox.files_download_to_file(tempfile_name, entry.path_display)

        with open(tempfile_name) as f:
            self._storage_image_writer(self._relative_path(entry.path_display), f)
        os.unlink(tempfile_name)

    def _storage_image_writer(self, path, f):
        try:
            image, created = Image.objects.get_or_create(path=path)
        except Image.MultipleObjectsReturned:
            images = Image.objects.filter(path=path)
            image = images[0]
            for i in images[1:]:
                i.delete()
        django_file = File(f)
        image.image.save(path, django_file)

    def _storage_file_writer(self, path, f):
        media_path = _media_path(None, path)
        django_file = File(f)
        StorageWithOverwrite().save(media_path, django_file)

    def _delete_file(self, path):
        logger.debug("Deleting %s", path)

        # cleanup database image with this name, if any
        try:
            # Dropbox returns only lower case name after delete
            image = Image.objects.get(path__iexact=self._relative_path(path))
            image_name = image.image.name
            image.delete()
            StorageWithOverwrite().delete(image_name)
        except Image.DoesNotExist, e:
            pass
