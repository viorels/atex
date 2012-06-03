from django.http import HttpResponse
from django.shortcuts import render

def products(request):
    products = [{'id': 1, 'name': 'Procesoare'},
                {'id': 2, 'name': 'Placi de baza'}]
    context = {'products': products}
    return render(request, "products.html", context)
