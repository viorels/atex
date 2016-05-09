from collections import OrderedDict
from django.contrib import admin
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import forms as auth_forms, get_user_model
from django.contrib.redirects.models import Redirect
from django import forms
from pathlib import Path

from .models import Category, Product, Image, Hit, Banner
from .dropbox_media import DropboxMedia
from .tasks import import_specs


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    readonly_fields = ('code', 'name')
    search_fields = ('name',)
    ordering = ('code',)
    fields = ('code', 'name', 'specs_file')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(parent=None)

    def save_model(self, request, obj, form, change):
        form.save()  # save file
        if self.accepted_file(obj.specs_file):
            result = import_specs.delay(obj.specs_file.path)
        else:
            obj.specs_file.delete()

    def accepted_file(self, file):
        return file.name.lower().endswith('.xlsx')

    def get_actions(self, request):
        actions = super().get_actions(request)
        del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None): # note the obj=None
        return False


class ImageCountListFilter(SimpleListFilter):
    title = _('Image count')
    parameter_name = 'image_count'

    def lookups(self, request, model_admin):
        return (
            ('0', _('No images')),
            ('1', _('Some images')),
        )

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.extra(where=['(%s) = 0' % queryset.image_subquery()])
        elif self.value() == '1':
            return queryset.extra(where=['(%s) > 0' % queryset.image_subquery()])


class ProductQuerySet(QuerySet):
    def image_subquery(self):
        return self._aggregate_related_subquery(Image)

    def hit_subquery(self):
        return (self._aggregate_related_subquery(Hit, aggregate='SUM(count)') +
                ' AND "atex_web_hit"."date" >= %s')

    def _aggregate_related_subquery(self, related_model, aggregate='COUNT(*)'):
        # info to build subquery
        # str(Image.objects.extra(select={'count': 'COUNT(*)'}, 
        #                         where=['atex_web_image.product_id = atex_web_product.id'])
        #                   .only()
        #                   .query)
        # self.connection.ops.quote_name
        args = {
            'aggregate': aggregate,
            'this_table': self.model._meta.db_table,
            'this_field': self.model._meta.get_field('id').column,
            'related_table': related_model._meta.db_table,
            'related_field': self._get_related_field(related_model).column
        }
        query = ('SELECT %(aggregate)s FROM "%(related_table)s" '
                 'WHERE "%(related_table)s"."%(related_field)s" = "%(this_table)s"."%(this_field)s"'
                 % args)
        return query

    def _get_related_field(self, related_model):
        """ Search the field on the related model that is connecting back to this model."""
        related_fields = [f for f in related_model._meta.fields
                          if f.rel and f.rel.to == self.model]
        return related_fields[0]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'folder_name', 'hit_count', 'image_count')
    search_fields = ('name',)
    list_filter = (ImageCountListFilter,)
    readonly_fields = ('name', 'model',)
    actions = ('action_create_dropbox_folder',)

    def action_create_dropbox_folder(self, request, queryset):
        dropbox = DropboxMedia()
        for product in queryset:
            if len(product.image_files()) == 0:
                dropbox.create_product_folder(product.folder_name())
        self.message_user(request, "Created %d product folders on Dropbox" % len(queryset))
    action_create_dropbox_folder.short_description = "Create Dropbox folders for selected products"

    def get_queryset(self, request):
        qs = ProductQuerySet(Product)
        hit_params = (Product.objects.one_month_ago(),)
        return (qs.extra(select=OrderedDict([('image_count', qs.image_subquery()),
                                             ('hit_count', qs.hit_subquery())]),
                         select_params=hit_params))

    def hit_count(self, obj):
        return obj.hit_count
    hit_count.admin_order_field = 'hit_count'

    def image_count(self, obj):
        count = obj.image_count
        if count > 0:
            return count
        else:
            return '<span style="color:#DF0101">%d</span>' % count
    image_count.admin_order_field = 'image_count'
    image_count.allow_tags = True


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = auth_forms.ReadOnlyPasswordHashField()

    class Meta:
        model = get_user_model()
        fields = ['email', 'password',
                  'is_active', 'is_staff', 'is_superuser',
                  'groups', 'user_permissions', 'last_login', 'date_joined',
                  'first_name', 'last_name']

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    error_messages = {
        'duplicate_email': _("A user with that email address already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(label=_("Password"),
        widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."))

    class Meta:
        model = get_user_model()
        fields = ("email",)

    def clean_email(self):
        # Since User.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        email = self.cleaned_data["email"]
        try:
            get_user_model()._default_manager.get(email=email)
        except get_user_model().DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_username'])

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

@admin.register(get_user_model())
class CustomUserAdmin(UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )

    list_display = ('email', "first_name", "last_name", "is_staff")
    list_filter = ('is_active',)
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('email',)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('name', 'image', 'order')
    list_editable = ('order',)
    list_display_links = ('name',)

    def name(self, obj):
        image_title = obj.title
        image_name = Path(obj.image.path).name
        return image_title or image_name
