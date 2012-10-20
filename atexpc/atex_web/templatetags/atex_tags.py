from django import template
from django.conf import settings
from sorl.thumbnail import get_thumbnail

register = template.Library()

@register.filter
def thumbnail(image, size):
    no_image_url = settings.STATIC_URL + "images/no-image-%s.jpg" % size
    if image.is_not_available():
        url = no_image_url
    else:
        try:
            thumb = get_thumbnail(image.image, size, upscale=False, quality=85)
            url = settings.MEDIA_URL + thumb.name
        except IOError, e:
            print e
            url = no_image_url
    return url
