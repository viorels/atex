from django.contrib import admin
from django.db.models import Count, Sum
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter

from models import Product, DropboxMedia


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
            return queryset.filter(image_count=0)
        elif self.value() == '1':
            return queryset.filter(image_count__gte=1)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('model', 'folder_name', 'hit_count', 'image_count')
    search_fields = ('^model',)
    # list_filter = (ImageCountListFilter,)
    readonly_fields = ('model',)
    actions = ('create_dropbox_folder',)

    def create_dropbox_folder(self, request, queryset):
        dropbox = DropboxMedia()
        for product in queryset:
            dropbox.create_product_folder(product.folder_name())
        self.message_user(request, "Created %d product folders on Dropbox" % len(queryset))
    create_dropbox_folder.short_description = "Create Dropbox folders for selected products"

    def queryset(self, request):
        return (Product.objects.filter(hit__date__gte=Product.objects.one_month_ago())
                               .annotate(hit_count=Sum('hit__count'),
                                         image_count=Count('image')))

    def hit_count(self, obj):
        return obj.hit_count
    hit_count.admin_order_field = 'hit_count'

    def image_count(self, obj):
        # TODO: use image_count (from database)
        count = len(obj.image_files())
        if count > 0:
            return count
        else:
            return '<span style="color:#DF0101">%d</span>' % count
    image_count.allow_tags = True

admin.site.register(Product, ProductAdmin)

admin.site.disable_action('delete_selected')