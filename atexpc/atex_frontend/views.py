from django.http import HttpResponse
from django.shortcuts import render

from models import ancora

def home(request):
    def category_icon(slug):
        mapping = {'1': 'images/desktop-icon.png',
                   '2': 'images/tv-icon.png',
                   '3': 'images/hdd-icon.png',
                   '4': 'images/mouse-icon.png',
                   '5': 'images/printer-icon.png',
                   '6': 'images/network-icon.png',
                   '7': 'images/cd-icon.png'}
        return mapping.get(slug[0], '')

    def category_background(slug):
        return "bg-%02d" % (int(slug[0]),)

    context = {'categories': ancora.get_categories(parent=None)}

    menu = []
    for cat in ancora.get_categories(parent=None):
        columns = [[]]
        for l2cat in ancora.get_categories(parent=cat['id']):
            for l3cat in ancora.get_categories(parent=l2cat['id']):
                columns[0].append({'name': l3cat['name'],
                                   'count': l3cat['count'],
                                   'level': 3})
            columns[0].append({'name': l2cat['name'],
                               'count': l2cat['count'],
                               'level': 2})

        category = {'name': cat['name'],
                    'icon': category_icon(cat['slug']),
                    'background': category_background(cat['slug']),
                    'columns': columns}
        print category
        menu.append(category)
        
    context['menu'] = menu
    
    return render(request, "home.html", context)

def products(request):
    context = {'categories': ancora.get_categories(parent=None)}
    return render(request, "products.html", context)

