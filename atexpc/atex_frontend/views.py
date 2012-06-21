from operator import itemgetter

from django.http import HttpResponse
from django.shortcuts import render

from models import ancora

def home(request):
    context = {'categories': ancora.get_categories(parent=None),
               'menu': _get_menu()}
    return render(request, "home.html", context)

def search(request):
    context = {'categories': ancora.get_categories(parent=None),
               'menu': _get_menu()}
    return render(request, "search.html", context)


def product(request):
    context = {'categories': ancora.get_categories(parent=None)}
    return render(request, "product.html", context)

def cart(request):
    context = {'categories': ancora.get_categories(parent=None),
               'menu': _get_menu()}
    return render(request, "cart.html", context)

def order(request):
    context = {'categories': ancora.get_categories(parent=None),
               'menu': _get_menu()}
    return render(request, "order.html", context)
    
def confirm(request):
    context = {'categories': ancora.get_categories(parent=None),
               'menu': _get_menu()}
    return render(request, "confirm.html", context)

def _get_menu():
    def category_icon(cat_id):
        icons = {'1': 'images/desktop-icon.png',
                 '2': 'images/tv-icon.png',
                 '3': 'images/hdd-icon.png',
                 '4': 'images/mouse-icon.png',
                 '5': 'images/printer-icon.png',
                 '6': 'images/network-icon.png',
                 '7': 'images/cd-icon.png',
                 '8': 'images/phone-icon.png'}
        return icons.get(cat_id, '')

    def category_background_class(cat_id):
        return "bg-%02d" % int(cat_id)

    menu = []
    for cat in ancora.get_categories(parent=None):
        category = {'name': cat['name'],
                    'icon': category_icon(cat['id']),
                    'background_class': category_background_class(cat['id'])}

        max_per_column = 10
        columns = [[], [], []]
        l2_categories = ancora.get_categories(parent=cat['id'])
        sorted_l2_categories = sorted(l2_categories, key=itemgetter('name'))
        for l2cat in sorted_l2_categories:
            l2cat_items = [{'name': l2cat['name'],
                            'count': l2cat['count'],
                            'level': 2}]
            for l3cat in ancora.get_categories(parent=l2cat['id']):
                l2cat_items.append({'name': l3cat['name'],
                                    'count': l3cat['count'],
                                    'level': 3})
            for column in columns:
                if len(column) + len(l2cat_items) <= max_per_column:
                    column.extend(l2cat_items)
                    break
        category['columns'] = columns

        menu.append(category)

    return menu

