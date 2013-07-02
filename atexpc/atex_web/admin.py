from django.contrib import admin
from django.db.models import Count, Sum
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.redirects.models import Redirect
from django.utils.datastructures import SortedDict

from models import Product, Image, Hit, UserProfile
from dropbox_media import DropboxMedia


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

    def queryset(self, request):
        qs = ProductQuerySet(Product)
        hit_params = (Product.objects.one_month_ago(),)
        return (qs.extra(select=SortedDict([('image_count', qs.image_subquery()),
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
admin.site.register(Product, ProductAdmin)


class RedirectAdmin(admin.ModelAdmin):
    actions = ('delete_selected',)
admin.site.unregister(Redirect)
admin.site.register(Redirect, RedirectAdmin)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = (UserProfileInline, )
    actions = ('delete_selected',)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


admin.site.disable_action('delete_selected')