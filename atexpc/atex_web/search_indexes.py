import datetime
from django.db.models import Prefetch, F, Sum
from haystack import indexes

from models import Product, Hit
from utils import one_month_ago


class ProductIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='get_best_name', boost=1.125)
    name_auto = indexes.EdgeNgramField(model_attr='get_short_name')
    main_category = indexes.IntegerField(model_attr='get_main_category_code', faceted=True)
    # brand = indexes.CharField(model_attr='brand__name', faceted=True)
    price = indexes.FloatField(model_attr='price')
    stock = indexes.IntegerField(model_attr='stock')
    hits = indexes.IntegerField()

    def get_model(self):
        return Product

    def build_queryset(self, *args, **kwargs):
        qs = super(ProductIndex, self).build_queryset(*args, **kwargs)

        recent_hits_qs = Hit.objects.filter(date__gte=one_month_ago())

        qs = qs.select_related('category') \
               .prefetch_related('specs') \
               .prefetch_related(Prefetch('hit_set', queryset=recent_hits_qs))
        return qs

    def prepare_hits(self, product):
        return sum(hit.count for hit in product.hit_set.all())

    def get_updated_field(self):
        return "updated"    # update_index --age=10 (hours)
