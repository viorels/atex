from atexpc.atex_web.models import Product
from django.db.models import Count


for dup in Product.objects.values('model').annotate(cnt=Count('id')).filter(cnt__ge=2):
    for p in Product.objects.filter(model=dup['model']):
        p.specs.all().delete()
        p.delete()

