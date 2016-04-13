import datetime
from haystack import indexes
from models import Product


class ProductIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='get_best_name', boost=2)
    name_auto = indexes.EdgeNgramField(model_attr='get_short_name')
    main_category = indexes.IntegerField(model_attr='get_main_category_code', faceted=True)
    # brand = indexes.CharField(model_attr='brand__name', faceted=True)
    price = indexes.FloatField(model_attr='price')
    stock = indexes.IntegerField(model_attr='stock')
    hits = indexes.IntegerField(model_attr='get_recent_hits')

    def get_model(self):
        return Product

    def build_queryset(self, *args, **kwargs):
        qs = super(ProductIndex, self).build_queryset(*args, **kwargs)
        qs = qs.select_related('category', 'brand') \
               .prefetch_related('specs')
        # TODO: prefetch recent hits
        return qs

    def get_updated_field(self):
        return "updated"    # update_index --age=10 (hours)
