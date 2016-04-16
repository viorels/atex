from __future__ import absolute_import

from celery.utils.log import get_task_logger
from django.core.cache import cache

from atexpc.celery import app
from atexpc.atex_web import specs_impex
from atexpc.atex_web.dropbox_media import DropboxMedia
from atexpc.atex_web.models import Product

logger = get_task_logger(__name__)

LOCK_EXPIRE = 60 * 5 # Lock expires in 5 minutes

@app.task
def import_specs(fname, ignore_result=True):
    return specs_impex.import_specs(fname)

@app.task(bind=True, ignore_result=True, default_retry_delay=15)
def sync_dropbox(self):
    lock_id = '{0}-lock'.format(self.name)
    acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)

    if acquire_lock():
        try:
            DropboxMedia().synchronize()
            Product.objects.assign_images()
        finally:
            release_lock()
    else:
        logger.debug('Dropbox sync already in progress')
        self.retry()
