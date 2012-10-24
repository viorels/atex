import re
import math
import os
from operator import itemgetter
from urlparse import urlparse, urlunparse, parse_qsl
from urllib import urlencode

from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.template import Context, Template
from django.views.generic.base import TemplateView
from django.conf import settings

from models import Product, Categories
from forms import search_form_factory

import logging
logger = logging.getLogger(__name__)


class GenericView(TemplateView):
    def __init__(self, *args, **kwargs):
        super(GenericView, self).__init__(*args, **kwargs)
        self.categories = Categories()

    def get_general_context(self):
        return {'menu': self.get_menu,
                'categories': self.categories.get_main,
                'footer': self.get_footer}

    def get_particular_context(self):
        return {}

    def get_context_data(self, **kwargs):
        context = super(GenericView, self).get_context_data(**kwargs)
        context.update(self.get_general_context())
        context.update(self.get_particular_context())
        return context

    def get_menu(self):
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

        def categories_in(category=None):
            parent_id = category['code'] if category is not None else None
            categories = self.categories.get_children(parent_id)
            sorted_categories = sorted(categories, key=itemgetter('code'))
            return sorted_categories

        def menu_category(category):
            """Prepare a category to be displayed in the menu"""
            menu_category = {'name': category['name'],
                             'url': _category_url(category),
                             'count': category['count'],
                             'level': _category_level(category)}
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

    def get_footer(self):
        return [{'name': category['name'],
                 'url': _category_url(category)}
                for category in self.categories.get_all()
                if _category_level(category) >= 2 and category['count'] > 0]


class BreadcrumbsMixin(object):
    def get_context_data(self, **kwargs):
        context = super(BreadcrumbsMixin, self).get_context_data(**kwargs)
        context.update({'breadcrumbs': self.get_breadcrumbs})
        return context

    def _get_search_breadcrumbs(self, search_keywords, category_id):
        breadcrumbs = []
        if search_keywords:
            breadcrumbs.append({'name': '"%s"' % search_keywords,
                                'url': None})
        elif category_id:
            breadcrumbs = self._get_category_breadcrumbs(category_id)
        if breadcrumbs:
            breadcrumbs[-1]['url'] = None # the current navigation item is not clickable
        return breadcrumbs

    def _get_category_breadcrumbs(self, category_id):
        breadcrumbs = []
        category = self.categories.get_category(category_id)
        while category is not None:
            crumb = {'name': category['name'],
                     'url': _category_url(category)}
            breadcrumbs.insert(0, crumb)
            category = self.categories.get_parent_category(category['id'])
        return breadcrumbs


class SearchMixin(object):
    def get_context_data(self, **kwargs):
        context = super(SearchMixin, self).get_context_data(**kwargs)
        context.update({'search_form': self.get_search_form})
        return context

    def get_search_form(self):
        search_in_choices = tuple((c['id'], c['name']) for c in self.categories.get_main())
        search_form_class = search_form_factory(search_in_choices, advanced=False)
        search_form = search_form_class(self.request.GET)
        return search_form


class HomeView(SearchMixin, GenericView):
    template_name = "home.html"
    top_limit = 5

    def get_particular_context(self):
        return {'hits': self.get_hits,
                'recommended': self.get_recommended,
                'promotional': self.get_promotional}

    def get_hits(self):
        hits = []
        product_objects = Product.objects.get_top_hits(limit=self.top_limit)
        product_ids = [p.ancora_id for p in product_objects]
        products = Product.objects.get_product_list(product_ids)
        print products
        for product_obj in product_objects:
            matching_in_backend = [p for p in products
                                   if int(p['id']) == product_obj.ancora_id]
            if matching_in_backend:
                product = matching_in_backend[0]
                product['images'] = product_obj.images
                product['url'] = _product_url(product)
                hits.append(product)
        return hits
    
    def get_recommended(self):
        recommended = Product.objects.get_recommended(limit=self.top_limit)
        for product in recommended:
            product['images'] = Product(model=product['model']).images
            product['url'] = _product_url(product)
        return recommended

    def get_promotional(self):
        promotional = Product.objects.get_promotional(limit=self.top_limit)
        for product in promotional:
            product['images'] = Product(model=product['model']).images
            product['url'] = _product_url(product)
        return promotional


class SearchView(BreadcrumbsMixin, GenericView):
    template_name = "search.html"

    def get_particular_context(self):
        return {'search_form': self.get_search_form,
                'selectors': self.get_selectors,
                'selectors_active': lambda: self.get_search_args()['selectors_active'],
                'products': self.get_products(),
                'pagination': self.get_pagination}

    def get_breadcrumbs(self):
        args = self.get_search_args()
        return self._get_search_breadcrumbs(args['keywords'], args['category_id'])

    def get_search_form(self):
        if not hasattr(self, '_search_form'):
            request_GET = self.request.GET.copy()
            if request_GET.get('categorie') is None:
                request_GET['categorie'] = self.get_category_id()
            search_in_choices = tuple((c['id'], c['name']) for c in self.categories.get_main())
            search_form_class = search_form_factory(search_in_choices, advanced=True)
            self._search_form = search_form_class(request_GET)
            if not self._search_form.is_valid():
                logger.error("search form errors: %s", self._search_form.errors)
        return self._search_form

    def get_search_args(self):
        defaults = {'category_id': '',
                    'keywords': '',
                    'current_page': 1,
                    'per_page': 20,
                    'price_min': '',
                    'price_max': '',
                    'selectors_active': [],
                    'stock': '',
                    'sort_by': 'pret',
                    'sort_order': 'asc'}
        args = {}
        search_form = self.get_search_form()
        if search_form.is_valid():
            args['category_id'] = self.get_category_id()
            args['keywords'] = search_form.cleaned_data.get('cuvinte')
            args['current_page'] = search_form.cleaned_data.get('pagina')
            args['per_page'] = search_form.cleaned_data.get('pe_pagina')
            args['price_min'] = search_form.cleaned_data.get('pret_min')
            args['price_max'] = search_form.cleaned_data.get('pret_max')

            args['selectors_active'] = self.request.GET.getlist('filtre')

            args['stock'] = self.request.GET.get('stoc')
            args['sort_by'], args['sort_order'] = self.request.GET.get('ordine', 'pret_asc').split('_')
        
        for key, default_value in defaults.items():
            if not args.get(key):
                args[key] = defaults[key]

        return args

    def get_category_id(self):
        return self.kwargs.get('category_id') or self.request.GET.get('categorie')

    def get_products_page(self):
        if not hasattr(self, '_products_page'):
            args = self.get_search_args()
            get_products_range = (lambda start, stop:
                Product.objects.get_products(
                    category_id=args['category_id'], keywords=args['keywords'],
                    selectors=args['selectors_active'], price_min=args['price_min'], 
                    price_max=args['price_max'], stock=args['stock'],
                    start=start, stop=stop,
                    sort_by=args['sort_by'], sort_order=args['sort_order']))
            self._products_page = self._get_page(
                get_products_range, per_page=args['per_page'],
                current_page=args['current_page'],
                base_url=self.request.build_absolute_uri())
        return self._products_page

    def _get_page(self, range_getter, per_page, current_page, base_url):
        start = (current_page - 1) * per_page
        stop = start + per_page
        data = range_getter(start, stop)

        total_count = data.get('total_count')
        start = min(start + 1, total_count) # humans start counting from 1
        stop = min(stop, total_count)

        pages_count = int(math.ceil(float(total_count)/per_page))
        page_info = lambda number: {
            'name': number,
            'url': _uri_with_args(base_url, pagina=number),
            'is_current': number==current_page}
        pages = [page_info(number) for number in range(1, pages_count + 1)]

        previous_page = page_info(current_page - 1) if current_page > 1 else None
        next_page = page_info(current_page + 1) if current_page < pages_count else None

        data['pagination'] = {'pages': pages,
                              'previous': previous_page,
                              'next': next_page,
                              'start': start,
                              'stop': stop,
                              'total_count': total_count}
        return data

    def get_products(self):
        products = self.get_products_page().get('products')
        for product in products:
            product['images'] = Product(model=product['model']).images
            product['url'] = _product_url(product)

        products_per_line = 4
        for idx, product in enumerate(products):
            if (idx+1) % products_per_line == 0:
                product['last_in_line'] = True

        return products

    def get_pagination(self):
        return self.get_products_page().get('pagination')

    def get_selectors(self):
        args = self.get_search_args()
        selectors = self.categories.get_selectors(
            category_id=args['category_id'], 
            selectors_active=args['selectors_active'],
            price_min=args['price_min'], price_max=args['price_max'])
        return selectors

class ProductView(SearchMixin, BreadcrumbsMixin, GenericView):
    template_name = "product.html"
    recommended_limit = 3

    def get_product(self):
        if not hasattr(self, '_product'):
            product_id = self.kwargs['product_id']
            product = Product.objects.get_product(product_id)
            product_obj = Product(model=product['model'])
            product['images'] = product_obj.images()
            html_template = product_obj.html_description()
            if html_template:
                product_prefix = settings.MEDIA_URL + product_obj.folder_path() + '/'
                context = Context({'PRODUCT_PREFIX': product_prefix})
                product['html_description'] = Template(html_template).render(context)

            _product_storage(product).hit()
            self._product = product
        return self._product

    def get_recommended(self):
        recommended = Product.objects.get_recommended(limit=self.recommended_limit)
        for product in recommended:
            product['images'] = Product(model=product['model']).images
            product['url'] = _product_url(product)
        return recommended

    def get_breadcrumbs(self):
        product = self.get_product()
        category = self.categories.get_category_by_code(product['category_code'])
        if category:
            breadcrumbs = self._get_category_breadcrumbs(category['id'])
            breadcrumbs.append({'name': product['name'],
                                'url': None})
        else:
            breadcrumbs = []
        return breadcrumbs

    def get_particular_context(self):
        return {'product': self.get_product,
                'recommended': self.get_recommended()}


def _uri_with_args(base_uri, **new_args):
    """Overwrite specified args in base uri. If any other multiple value args
    are present in base_uri then they must be preserved"""
    parsed_uri = urlparse(base_uri)

    parsed_args = parse_qsl(parsed_uri.query)
    updated_args = [(key, value) for key, value in parsed_args if key not in new_args]
    updated_args.extend(new_args.items())
    valid_args = [(key, value) for key, value in updated_args if value is not None]
    encoded_args = urlencode(valid_args, doseq=True)

    final_uri = urlunparse((parsed_uri.scheme,
                            parsed_uri.netloc,
                            parsed_uri.path,
                            parsed_uri.params,
                            encoded_args,
                            parsed_uri.fragment))
    return final_uri

def _product_url(product):
    return reverse('product', kwargs={'product_id': product['id'],
                                      'slug': slugify(product['name'])})

def _category_url(category):
    if re.match(r'^\d+$', category['id']):
        category_url = reverse('category', kwargs={'category_id': category['id'],
                                                   'slug': slugify(category['name'])})
    else:
        category_url = None
    return category_url

def _category_level(category):
    return category['code'].count('.') + 1

def _product_storage(product):
    ancora_id = int(product['id'])
    product_info = {'ancora_id': ancora_id}
    product_obj, created = Product.objects.get_or_create(model=product['model'],
                                                         defaults=product_info)
    if not created and not product_obj.ancora_id:
        product_obj.ancora_id = ancora_id
        product_obj.save()
    return product_obj
