from django import template
from django.conf import settings
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from sorl.thumbnail import get_thumbnail
from urllib import urlencode
from urlparse import urlparse, urlunparse, parse_qsl
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
            thumb = get_thumbnail(image.image, size, upscale=False, padding=True, background='#fff', quality=85)
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

@register.simple_tag(takes_context=True)
def request_uri_with_args(context, **new_args):
    """Overwrite specified args in base uri. If any other multiple value args
    are present in base_uri then they must be preserved"""
    base_uri = context.request.build_absolute_uri()
    parsed_uri = urlparse(base_uri)

    parsed_args = parse_qsl(parsed_uri.query)
    updated_args = [(key, value) for key, value in parsed_args if key not in new_args]
    updated_args.extend(new_args.items())
    valid_args = [(key, value) for key, value in updated_args if value is not None]
    encoded_args = urlencode(valid_args, doseq=True)

    final_uri = urlunparse((parsed_uri.scheme,
                            parsed_uri.netloc,
                            parsed_uri.path,
                            parsed_uri.params,
                            encoded_args,
                            parsed_uri.fragment))
    return final_uri
