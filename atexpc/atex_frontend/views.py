from django.http import HttpResponse
from django.shortcuts import render
import datetime

def home(request):
    context = {}
    return render(request, "home.html", context)

def products(request):
    products = [{'id': 1, 'name': 'Procesoare'},
                {'id': 2, 'name': 'Placi de baza'}]
    context = {'categories': products}
    return render(request, "products.html", context)
