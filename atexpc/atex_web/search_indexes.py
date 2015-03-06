import datetime
from haystack import indexes
from models import Product


class ProductIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='get_best_name', boost=2)
    # category = indexes.CharField(model_attr='category__name', boost=0.8)
    # stock = indexes.BooleanField(model_attr='stock')

    def get_model(self):
        return Product
