import os
import re
from datetime import datetime, timedelta

import pytz
from django.db import models
from django.db.models.query import QuerySet
from django.core.files.storage import get_storage_class
from django.template.defaultfilters import slugify
from sorl.thumbnail import ImageField

import logging
logger = logging.getLogger(__name__)


class ProductManager(models.Manager):
    def _build_folder_product_map(self):
        """ Builds a map from lowercase folder name (as found on Dropbox) to product id"""
        folder_product = {}
        for product in self.all().iterator():
            folder_name = product.folder_name().lower()
            if folder_name not in folder_product:
                folder_product[folder_name] = product.id
            else:
                logger.warning("Products %d and %d map to the same folder",
                               folder_product[folder_name], product.id)
        return folder_product

    def assign_images(self):
        folder_product_map = self._build_folder_product_map()
        map_getter = lambda folder_name: folder_product_map.get(folder_name)
        Image.objects.all().assign_all_unasigned(get_product_id_for_folder=map_getter)

    def store(self, product_raw, update=False):
        """Save product basic details in database"""
        product_id = int(product_raw['id'])
        product_fields = dict((field.name, product_raw.get(field.name))
                              for field in Product._meta.fields)
        product, created = Product.objects.get_or_create(
            id=product_id, defaults=product_fields)
        if created:
            Image.objects.all().assign_images_folder_to_product(product)
        elif update:
            product.update(product_fields)
        return product

    def augment_with_hits(self, products):
        product_ids = [int(product['id']) for product in products]
        product_objs = (self.filter(hit__date__gte=self.one_month_ago())
                            .annotate(month_count=models.Sum('hit__count'))
                            .in_bulk(product_ids))
        for product in products:
            product_obj = product_objs.get(int(product['id']))
            product['hits'] = product_obj.month_count if product_obj else 0
        return products

    def get_top_hits(self, limit=5):
        return (self.filter(hit__count__gte=1,
                            hit__date__gte=self.one_month_ago())
                    .annotate(month_count=models.Sum('hit__count'))
                    .order_by('-month_count')[:limit])

    def one_month_ago(self):
        return datetime.now(pytz.utc).date() - timedelta(days=30)


class StorageWithOverwrite(get_storage_class()):
    """Storage that unconditionally overwrites files"""

    def get_available_name(self, name):
        self.delete(name)
        return name


class Product(models.Model):
    model = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=128)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)
    # has_folder = models.NullBooleanField()

    objects = ProductManager()

    media_folder = "products"
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    html_extensions = ('.html', '.htm')

    def __init__(self, *args, **kwargs):
        if kwargs.has_key('raw'):
            self.raw = kwargs.pop('raw')
            for field in self._meta.fields:
                kwargs[field.name] = self.raw.get(field.name)
        super(Product, self).__init__(*args, **kwargs)

    def folder_name(self):
        folder = re.sub(r'[<>:"|?*/\\]', "-", self.model)
        return folder

    def folder_path(self):
        return os.path.join(self.media_folder, self.folder_name())

    def _file_path(self, name):
        return os.path.join(self.folder_path(), name)

    def _product_files(self):
        try:
            folders, files = StorageWithOverwrite().listdir(self.folder_path())
        except OSError, e:
            files = []
        return files

    def image_files(self):
        files = self._product_files()
        return [name for name in files if name.endswith(self.image_extensions)]

    def images(self):
        image_files = sorted(self.image_files())
        if len(image_files):
            images = [Image(image=self._file_path(name)) for name in image_files]
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

    @models.permalink
    def get_absolute_url(self):
        # TODO: store self.name on object and use it in url
        return ('product', (), {'product_id': self.id,
                                'slug': slugify(self.model)})

    def __unicode__(self):
        return self.model


class CustomQuerySetManager(models.Manager):
    """A re-usable Manager to access a custom QuerySet"""
    def get_query_set(self):
        return self.model.QuerySet(self.model)


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
    objects = CustomQuerySetManager()

    class QuerySet(QuerySet):
        def unassigned(self, *args, **kwargs):
            return self.filter(product=None, *args, **kwargs)

        def in_folder(self, folder_name, *args, **kwargs):
            path = "%s/%s/" % (Product.media_folder, folder_name)
            return self.filter(image__istartswith=path, *args, **kwargs)

        def assign_images_folder_to_product(self, product):
            folder_name = product.folder_name()
            self.unassigned().in_folder(folder_name).update(product=product)

        def assign_all_unasigned(self, get_product_id_for_folder=lambda folder_name: None):
            for image in self.unassigned().iterator():
                folder_name = image.folder_name().lower()
                product_id = get_product_id_for_folder(folder_name)
                if product_id is not None:
                    image.product_id = product_id
                    image.save()
                    logger.debug("Assigned image %s to product id %d", image, product_id)

    def folder_name(self):
        path_match = re.match(Product.media_folder + r'/([^/]+)', self.image.name)
        folder = path_match.group(1) if path_match else None
        return folder

    NO_IMAGE = 'no-image'
    def is_not_available(self):
        return self.image == self.NO_IMAGE

    @classmethod
    def not_available(cls):
        return Image(image=cls.NO_IMAGE)

    def __unicode__(self):
        return self.image.name


class Hit(models.Model):
    product = models.ForeignKey(Product, unique_for_date="date")
    count = models.IntegerField()
    date = models.DateField()


class Dropbox(models.Model):
    app_key = models.CharField(primary_key=True, max_length=64)
    delta_cursor = models.CharField(max_length=512, blank=True, null=True)
