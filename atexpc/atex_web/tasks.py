from __future__ import absolute_import

from atexpc.celery import app
from atexpc.atex_web import specs_impex

@app.task
def import_specs(fname):
    return specs_impex.import_specs(fname)
