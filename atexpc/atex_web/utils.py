from datetime import datetime, timedelta
from operator import itemgetter
from itertools import groupby, chain, repeat
from collections import Mapping

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import pytz
from PIL import Image, ImageColor
from sorl.thumbnail.engines.pil_engine import Engine


class LoginRequiredMixin:
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


def group_in(n, items):
    return [[item for i, item in group] for i, group
            in groupby(sorted((i % n, item) for i, item in enumerate(items)),
                       itemgetter(0))]


def grouper(n, iterable, padvalue=None):
    "grouper(3, 'abcdefg', 'x') --> ('a','b','c'), ('d','e','f'), ('g','x','x')"
    return zip(*[chain(iterable, repeat(padvalue, n-1))]*n)

def one_month_ago():
    return datetime.now(pytz.utc).date() - timedelta(days=30)

class FrozenDict(Mapping):
    """ Immutable dictionary """

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        self._hash = None

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __getitem__(self, key):
        return self._d[key]

    def __hash__(self):
        # It would have been simpler and maybe more obvious to
        # use hash(tuple(sorted(self._d.iteritems()))) from this discussion
        # so far, but this solution is O(n). I don't know what kind of
        # n we are going to run into, but sometimes it's hard to resist the
        # urge to optimize when it will gain improved algorithmic performance.
        if self._hash is None:
            self._hash = 0
            for pair in self.iteritems():
                self._hash ^= hash(pair)
        return self._hash

    def copy(self):
        return self._d.copy()


class BackgroundColorEngine(Engine):
    """Conversion engine for PNG->JPG with correct background collor"""
    def create(self, image, geometry, options):
        thumb = super(Engine, self).create(image, geometry, options)
        if options.get('background'):
            try:
                background = Image.new('RGB', thumb.size, ImageColor.getcolor(options.get('background'), 'RGB'))
                background.paste(thumb, mask=thumb.split()[3]) # 3 is the alpha of an RGBA image.
                return background
            except Exception as e:
                return thumb
        return thumb
