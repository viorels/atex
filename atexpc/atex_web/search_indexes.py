import datetime
from haystack import indexes
from models import Product


class ProductIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    category = indexes.CharField(model_attr='category')
    updated = indexes.DateTimeField(model_attr='updated')
    # stock = indexes.BooleanField(model_attr='stock')

    def get_model(self):
        return Product
