from django import template
from django.conf import settings
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from sorl.thumbnail import get_thumbnail
import json


import logging
logger = logging.getLogger(__name__)

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
            logger.debug("%s: %s", image.image, e)
            url = no_image_url
        except IndexError, e:
            # string index out of range 
            # at lib/python2.6/site-packages/PIL/TiffImagePlugin.py in il16, line 68
            logger.debug("%s: %s", image.image, e)
            url = no_image_url
    return url

@register.filter
def jsonify(object):
    if isinstance(object, QuerySet):
        return serialize('json', object)
    return json.dumps(object)
