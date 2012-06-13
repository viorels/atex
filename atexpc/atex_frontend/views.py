from django.http import HttpResponse
from django.shortcuts import render

from models import ancora

def home(request):
    context = {}
    return render(request, "home.html", context)

def products(request):
    context = {'categories': ancora.get_categories(parent=None)}
    return render(request, "products.html", context)

