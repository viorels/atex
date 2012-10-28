from django.contrib import admin
from models import Product, DropboxMedia


class ProductAdmin(admin.ModelAdmin):
    readonly_fields = ('model',)
    actions = ('create_dropbox_folder',)

    def create_dropbox_folder(self, request, queryset):
        dropbox = DropboxMedia()
        for product in queryset:
            dropbox.create_product_folder(product.folder_name())
        self.message_user(request, "Created %d product folders on Dropbox" % len(queryset))
    create_dropbox_folder.short_description = "Create Dropbox folders for selected products"

admin.site.register(Product, ProductAdmin)