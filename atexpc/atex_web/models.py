import os
import re
import shutil
from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.db import models
from django.core.files import File, temp
from django.core.files.storage import get_storage_class
from sorl.thumbnail import ImageField
from dropbox import rest, session, client

from atexpc.ancora_api.api import Ancora, AncoraAdapter, MockAdapter, MOCK_DATA_PATH

import logging
logger = logging.getLogger(__name__)

class StorageWithOverwrite(get_storage_class()):
    """Storage that unconditionally overwrites files"""

    def get_available_name(self, name):
        self.delete(name)
        return name


class ProductManager(models.Manager):
    def get_top_hits(self, limit=5):
        one_month_ago = datetime.now(pytz.utc).date() - timedelta(days=30)
        return (self.filter(hit__count__gte=1,
                            hit__date__gte=one_month_ago)
                    .annotate(month_count=models.Sum('hit__count'))
                    .order_by('-month_count')[:limit])


class Product(models.Model):
    model = models.CharField(max_length=64, unique=True)
    ancora_id = models.IntegerField(null=True)

    objects = ProductManager()

    media_folder = "products"
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    html_extensions = ('.html', '.htm')

    def _folder_name(self):
        folder = re.sub(r'[<>:"|?*/\\]', "-", self.model)
        return folder

    def folder_path(self):
        return os.path.join(self.media_folder, self._folder_name())

    def _file_path(self, name):
        return os.path.join(self.folder_path(), name)

    def _product_files(self):
        try:
            folders, files = StorageWithOverwrite().listdir(self.folder_path())
        except OSError, e:
            files = []
        return files

    def images(self):
        files = self._product_files()
        image_files = [name for name in files if name.endswith(self.image_extensions)]
        if len(image_files):
            images = [Image(image=self._file_path(name)) for name in sorted(image_files)]
        else:
            images = [Image.not_available()]
        return images

    def html_description(self):
        files = self._product_files()
        html_files = [name for name in files if name.endswith(self.html_extensions)]
        if len(html_files):
            html_path = self._file_path(html_files[0])
            content = StorageWithOverwrite().open(html_path).read()
        else:
            content = None
        return content

    def hit(self):
        today = datetime.now(pytz.utc).date()
        hit_info = {'count': 1}
        hit, created = Hit.objects.get_or_create(product=self, date=today,
                                                 defaults=hit_info)
        if not created:
            hit.count = models.F('count') + 1
            hit.save()


class Image(models.Model):
    def _media_path(instance, filename):
        if '/' in filename:
            path_match = re.search(Product.media_folder + '.*', filename)
            path = path_match.group()
        else:
            path = os.path.join(Product.media_folder, filename)
        return path
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    path = models.CharField(max_length=128, db_index=True)
    image = ImageField(storage=StorageWithOverwrite(), upload_to=_media_path, max_length=255)

    NO_IMAGE = 'no-image'
    def is_not_available(self):
        return self.image == self.NO_IMAGE

    @classmethod
    def not_available(cls):
        return Image(image=cls.NO_IMAGE)


class Hit(models.Model):
    product = models.ForeignKey(Product, unique_for_date="date")
    count = models.IntegerField()
    date = models.DateField()


class Dropbox(models.Model):
    app_key = models.CharField(primary_key=True, max_length=64)
    delta_cursor = models.CharField(max_length=255, blank=True, null=True)


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
            state.delta_cursor = new_cursor
            state.save()
        return state.delta_cursor

    def create_product_folder(self, model):
        name = Product(model=model).folder_name()
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
        dropbox_file = self._dropbox.get_file(path, rev)

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


class AncoraBackend(object):
    def __init__(self):
        mock = MockAdapter('file://%s' % MOCK_DATA_PATH)
        ancora = AncoraAdapter(settings.ANCORA_URI)
        self._api = Ancora(adapter=ancora)

    def get_all_categories(self):
        all_valid = [category for category in self._api.categories()
                     if category['code'][0].isdecimal()] # skip "diverse" with code "XX"
        return all_valid

    def get_categories_in(self, parent=None):
        categories = [c for c in self.get_all_categories() if c['parent'] == parent]
        return categories

    def get_category(self, category_id, all_categories=None):
        if category_id is None:
            return None
        if all_categories is None:
            all_categories = self.get_all_categories()
        categories = [c for c in all_categories if c['id'] == category_id]
        if len(categories) == 1:
            return categories[0]
        else:
            return None

    def get_category_by_code(self, category_code, all_categories=None):
        if category_code is None:
            return None
        if all_categories is None:
            all_categories = self.get_all_categories()
        categories = [c for c in all_categories if c['code'] == category_code]
        if len(categories) == 1:
            return categories[0]
        else:
            return None 

    def get_parent_category(self, category_id, all_categories=None):
        if category_id is None:
            return None
        if all_categories is None:
            all_categories = self.get_all_categories()
        category = self.get_category(category_id, all_categories)
        category_code_parts = category['code'].split('.')
        parent_category_code_parts = category_code_parts[:-1]
        if parent_category_code_parts:
            parent_category_code = '.'.join(parent_category_code_parts)
            parent_categories = [c for c in all_categories if c['code'] == parent_category_code]
            if len(parent_categories) == 1:
                parent_category = parent_categories[0]
            else:
                parent_category = None
        else:
            parent_category = None
        return parent_category

    def get_top_category_id(self, category_id):
        category = self.get_category(category_id)
        parent_category_code = category['code'].split('.')[0]
        return [c for c in self.get_all_categories() if c['code'] == parent_category_code][0]['id']

    def get_selectors(self, category_id, selectors_active, price_min, price_max):
        return self._api.selectors(category_id, selectors_active,
                                   price_min=price_min, price_max=price_max)

    def get_products(self, category_id, keywords, selectors,
                     price_min, price_max, start, stop,
                     stock, sort_by, sort_order):
        return self._api.search_products(category_id=category_id, keywords=keywords,
                                         selectors=selectors, price_min=price_min,
                                         price_max=price_max, start=start, stop=stop,
                                         stock=stock, sort_by=sort_by, sort_order=sort_order)
        
    def get_product(self, product_id):
        return self._api.product(product_id)

    def get_recommended(self, limit):
        return self._api.products_recommended(limit)

    def get_sales(self, limit):
        return self._api.products_sales(limit)

ancora = AncoraBackend()

