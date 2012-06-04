from django.http import HttpResponse
from django.shortcuts import render

from ancora_api.api import Ancora, MockAdapter

def home(request):
    context = {}
    return render(request, "home.html", context)

def products(request):
    mock = MockAdapter('file:///home/vio/work/atex/atexpc/ancora_api/mock_data/')
    ancora = Ancora(adapter=mock)
    categories = ancora.categories()
    top_categories = [c for c in categories if c['id'].count('.') == 0]
    context = {'categories': top_categories}

    return render(request, "products.html", context)
