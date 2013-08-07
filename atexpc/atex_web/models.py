import os
import re
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.sessions.models import Session
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.files.storage import get_storage_class
from django.core.mail import send_mail
from django.db import models, connection
from django.db.models.query import QuerySet
from django.db.utils import DatabaseError
from django.utils import timezone
from django.utils.datastructures import SortedDict
from django.utils.http import urlquote
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
import pytz
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
    model = models.CharField(max_length=128, db_index=True)
    name = models.CharField(max_length=128)
    specs = models.ManyToManyField('Specification', through='ProductSpecification')
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

    def get_best_name(self):
        better_name = self.get_spec('Denumire')
        return better_name if better_name else self.name

    def get_spec(self, name):
        try:
            spec = Specification.objects.get(name=name)
            prod_spec = ProductSpecification.objects.get(product=self, spec=spec)
            spec_value = prod_spec.value
        except (Specification.DoesNotExist, ProductSpecification.DoesNotExist):
            spec_value = None
        return spec_value

    def specs_list(self):
        return SortedDict([(prod_spec.spec.name, prod_spec.value) 
            for prod_spec in ProductSpecification.objects
                .filter(product=self)
                .order_by('id')])

    def update_specs(self, specs):
        for spec in specs:
            try:
                spec_group, _ = SpecificationGroup.objects.get_or_create(name=spec.group)
                spec_obj, _ = Specification.objects.get_or_create(
                    name=spec.name, group=spec_group)
                ProductSpecification.objects.get_or_create(
                    product=self, spec=spec_obj, value=spec.value)
            except DatabaseError as e:
                connection._rollback()
                logger.error("failed to save spec %s for product %s: %s",
                    spec, self.model, e)

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
    product = models.ForeignKey(Product)
    count = models.IntegerField()
    date = models.DateField()

    class Meta:
        unique_together = ("product", "date")


class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('The given email address must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, last_login=now,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True,
                                 **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), blank=False, unique=True, db_index=True)
    ancora_id = models.IntegerField(blank=True, null=True)

    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_absolute_url(self):
        return "/users/%s/" % urlquote(self.email)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])


# class Company(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL)


class Cart(models.Model):
    session = models.ForeignKey(Session, db_index=True, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    products = models.ManyToManyField(Product, through='CartProducts')


class CartProducts(models.Model):
    cart = models.ForeignKey(Cart)
    product = models.ForeignKey(Product)
    count = models.IntegerField(default=1)


class BaseCart(object):
    def __init__(self, cart):
        self._cart = cart

    def count(self):
        return len(self.items())

    @staticmethod
    def price(items):
        return sum(item['count'] * item['product']['price'] for item in items)

    def _get_db_product(self, id):
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist as e:
            logger.error(e)
        else:
            return product


class CartFactory(object):
    def __init__(self, database=None, api=None):
        if not (database or api):
            raise ValueError("Specify either database (True) or api")
        self.database = database
        self.api = api

    def get(self, cart_id):
        if self.database:
            try:
                cart_row = Cart.objects.get(id=cart_id)
                cart = DatabaseCart(cart_row)
            except Cart.DoesNotExist:
                cart = None
        elif self.api:
            cart_id = self.api.cart.get_cart(cart_id)
            cart = AncoraCart(cart=cart_id, api=self.api)
        return cart

    def create(self, user_id=None):
        if self.database:
            cart_row = Cart.objects.create()
            cart = DatabaseCart(cart=cart_row)
        elif self.api:
            cart_id = self.api.cart.create_cart(user_id)
            cart = AncoraCart(cart=cart_id, api=self.api)
        return cart


class DatabaseCart(BaseCart):
    def id(self):
        return self._cart.id

    def items(self):
        cart_items = CartProducts.objects.filter(cart=self._cart)
        items = []
        for cart_item in cart_items:
            product = cart_item.product
            product_dict = {'id': product.id,
                            'name': product.get_best_name(),
                            'images': product.images()}
            item = {'product': product_dict,
                    'count': cart_item.count}
            items.append(item)
        return items

    def delivery_price(self, items):
        return 15 if items else 0  # TODO: compute price for delivery

    def add_item(self, product_id):
        product = self._get_db_product(product_id)
        if product:
            cart_product, created = CartProducts.objects.get_or_create(cart=self._cart, product=product)
            if not created:
                cart_product.count = models.F('count') + 1
                cart_product.save()
        return product

    def remove_item(self, product_id):
        product = self._get_db_product(product_id)
        if product:
            try:
                cart_product = CartProducts.objects.get(cart=self._cart, product=product)
            except CartProducts.DoesNotExist as e:
                logger.error(e)
                product = None
            else:
                cart_product.delete()
        return product

    def update_item(self, product_id, count):
        if count < 0:
            return
        if count == 0:
            return self.remove_item(product_id)
        product = self._get_db_product(product_id)
        if product:
            try:
                cart_product = CartProducts.objects.get(cart=self._cart, product=product)
            except CartProducts.DoesNotExist as e:
                logger.error(e)
            else:
                cart_product.count = count
                cart_product.save()


class AncoraCart(BaseCart):
    def __init__(self, cart, api):
        self._api = api
        super(AncoraCart, self).__init__(cart)

    def id(self):
        return self._cart

    def items(self):
        cart_items = self._api.cart.list_cart(self.id())
        items = []
        for cart_item in cart_items:
            product_id = cart_item['product_id']
            db_product = self._get_db_product(product_id)
            product_dict = {'id': product_id,
                            'name': db_product.get_best_name(),
                            'images': db_product.images()}
            item = {'product': product_dict,
                    'count': cart_item['quantity']}
            items.append(item)
        return items

    def delivery_price(self, items):
        return 15 if items else 0  # TODO: compute price for delivery

    def add_item(self, product_id):
        return self._api.cart.add_product(self.id(), product_id)

    def remove_item(self, product_id):
        return self._api.cart.remove_product(self.id(), product_id)

    def update_item(self, product_id, count):
        if count < 0:
            return
        if count == 0:
            return self.remove_item(product_id)
        return self._api.cart.update_product(self.id(), product_id, count)


class Dropbox(models.Model):
    app_key = models.CharField(primary_key=True, max_length=64)
    delta_cursor = models.CharField(max_length=512, blank=True, null=True)


class SpecificationGroup(models.Model):
    name = models.CharField(max_length=64)
#    category_id = models.IntegerField()


class Specification(models.Model):
    name = models.CharField(max_length=64)
    group = models.ForeignKey(SpecificationGroup, null=True)
#    category_id = models.IntegerField()


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product)
    spec = models.ForeignKey(Specification)
    value = models.CharField(max_length=255, blank=True)
