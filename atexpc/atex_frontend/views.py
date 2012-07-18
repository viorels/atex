import re
from operator import itemgetter

from django.http import HttpResponse
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

from models import ancora

import logging
logger = logging.getLogger(__name__)

def home(request):
    context = {'categories': ancora.get_categories_in(parent=None),
               'menu': _get_menu(),
               'footer': _get_footer()}
    return render(request, "home.html", context)

def search(request, category_id=None, slug=None):
    if not category_id:
        category_id = request.GET.get('categorie')
    search_keywords = request.GET.get('cuvinte')
    products = ancora.get_products(category_id=category_id, keywords=search_keywords)

    products_per_line = 4
    for idx, product in enumerate(products):
        if (idx+1) % products_per_line == 0:
            product['last_in_line'] = True

    context = {'categories': ancora.get_categories_in(parent=None),
               'menu': _get_menu(),
               'search_keywords': search_keywords,
               'category_id': category_id,
               'products': products,
               'footer': _get_footer()}
    return render(request, "search.html", context)

def product(request):
    context = {'categories': ancora.get_categories_in(parent=None),
               'footer': _get_footer()}
    return render(request, "product.html", context)

def cart(request):
    context = {'categories': ancora.get_categories_in(parent=None),
               'menu': _get_menu(),
               'footer': _get_footer()}
    return render(request, "cart.html", context)

def order(request):
    context = {'categories': ancora.get_categories_in(parent=None),
               'menu': _get_menu(),
               'footer': _get_footer()}
    return render(request, "order.html", context)
    
def confirm(request):
    context = {'categories': ancora.get_categories_in(parent=None),
               'menu': _get_menu(),
               'footer': _get_footer()}
    return render(request, "confirm.html", context)

def pie(request):
    return render(request, "PIE.htc", content_type="text/x-component")

def _get_menu():
    def category_icon(category):
        icons = {'1': 'images/desktop-icon.png',
                 '2': 'images/tv-icon.png',
                 '3': 'images/hdd-icon.png',
                 '4': 'images/mouse-icon.png',
                 '5': 'images/printer-icon.png',
                 '6': 'images/network-icon.png',
                 '7': 'images/cd-icon.png',
                 '8': 'images/phone-icon.png'}
        return icons.get(category['code'], '')

    def category_background_class(category):
        try:
            background_class = "bg-%02d" % int(category['code'])
        except ValueError, e:
            background_class = ""
        return background_class

    def category_url(category):
        if re.match(r'^[0-9.]+$', category['id']):
            category_url = reverse('category', kwargs={'category_id': category['id'],
                                                       'slug': slugify(category['name'])})
        else:
            category_url = None
        return category_url

    def category_level(category):
        return category['code'].count('.') + 1

    all_categories = ancora.get_all_categories()
    def categories_in(category=None):
        """Return chilid categories for the specified category
           or top categories if None specified"""
        if category is None:
            parent_id = None
        else:
            parent_id = category['code']
        categories = [c for c in all_categories if c['parent'] == parent_id]
        sorted_categories = sorted(categories, key=itemgetter('code'))
        return sorted_categories

    def menu_category(category):
        """Prepare a category to be displayed in the menu"""
        menu_category = {'name': category['name'],
                         'url': category_url(category),
                         'count': category['count'],
                         'level': category_level(category)}
        return menu_category

    menu = []
    max_per_column = 10
    for top_category in categories_in(None):
        columns = [[], [], []]
        for level2_category in categories_in(top_category):
            submenu_items = ([menu_category(level2_category)] + 
                             [menu_category(level3_category) 
                              for level3_category in categories_in(level2_category)])

            # insert into the first column with enough enough space
            for column in columns:
                if len(column) + len(submenu_items) <= max_per_column:
                    column.extend(submenu_items)
                    break
            # TODO: what if none has enough space ... MISSING CATEGORIES !!!

        category = menu_category(top_category)
        category.update({'columns': columns,
                         'icon': category_icon(top_category),
                         'background_class': category_background_class(top_category)})
        menu.append(category)

    return menu

def _get_footer():
    return ancora.get_all_categories()

