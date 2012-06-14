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
        max_per_column = 12
        columns = [[]]
        for l2cat in ancora.get_categories(parent=cat['id']):
            l2cat_items = [{'name': l2cat['name'],
                            'count': l2cat['count'],
                            'level': 2}]
            for l3cat in ancora.get_categories(parent=l2cat['id']):
                l2cat_items.append({'name': l3cat['name'],
                                    'count': l3cat['count'],
                                    'level': 3})
            if len(columns[-1]) + len(l2cat_items) > max_per_column:
                columns.append([])
            columns[-1].extend(l2cat_items)

        category = {'name': cat['name'],
                    'icon': category_icon(cat['slug']),
                    'background': category_background(cat['slug']),
                    'columns': columns}
        menu.append(category)
        
    context['menu'] = menu
    
    return render(request, "home.html", context)

def products(request):
    context = {'categories': ancora.get_categories(parent=None)}
    return render(request, "products.html", context)

