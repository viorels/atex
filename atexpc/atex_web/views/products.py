import math

from django.template import Context, Template
from django.http import Http404
from django.conf import settings

from atexpc.atex_web.views.base import BaseView
from atexpc.atex_web.models import Product, ProductSpecification
from atexpc.atex_web.forms import search_form_factory
from atexpc.atex_web.utils import group_in, grouper

import logging
logger = logging.getLogger(__name__)


class HomeBase(BaseView):
    template_name = "home.html"
    top_limit = 5

    def get_local_context(self):
        return {'hits': self.get_hits(),
                'recommended': self.get_recommended(),
                'promotional': self.get_promotional()}

    def get_hits(self):
        hits = []
        product_objects = Product.objects.get_top_hits(limit=self.top_limit)
        product_ids = [p.id for p in product_objects]
        products = self.api.products.get_product_list(product_ids)
        for product_obj in product_objects:
            matching_in_backend = [p for p in products
                                   if int(p['id']) == product_obj.id]
            if matching_in_backend:
                product = matching_in_backend[0]
                product['name'] = product_obj.get_short_name()
                product['images'] = product_obj.images
                product['url'] = self._product_url(product)
                hits.append(product)
        return hits

    def get_recommended(self):
        recommended = self.api.products.get_recommended(limit=self.top_limit)
        for product in recommended:
            product_obj = Product(raw=product)
            product['name'] = product_obj.get_short_name()
            product['images'] = product_obj.images
            product['url'] = self._product_url(product)
        return recommended

    def get_promotional(self):
        promotional = self.api.products.get_promotional(limit=self.top_limit)
        for product in promotional:
            product_obj = Product(raw=product)
            product['name'] = product_obj.get_short_name()
            product['images'] = product_obj.images
            product['url'] = self._product_url(product)
        return promotional


class SearchBase(BaseView):
    template_name = "search.html"

    def get_local_context(self):
        return {'search_form': self.get_search_form,
                'selectors': self.get_selectors,
                'selectors_active': lambda: self.get_search_args()['selectors_active'],
                'price_min': lambda: self.get_search_args()['price_min'],
                'price_max': lambda: self.get_search_args()['price_max'],
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
            search_in_choices = tuple((c['id'], c['name']) for c in self.api.categories.get_main())
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
        category_id = self.kwargs.get('category_id') or self.request.GET.get('categorie')
        return int(category_id) if category_id else None

    def get_products_page(self):
        if not hasattr(self, '_products_page'):
            args = self.get_search_args()
            products_args = {
                'category_id': args['category_id'], 'keywords': args['keywords'],
                'selectors': args['selectors_active'], 'price_min': args['price_min'],
                'price_max': args['price_max'], 'stock': args['stock'],
                'sort_by': args['sort_by'], 'sort_order': args['sort_order']}
            if args['sort_by'] == "vanzari":
                get_products_range = (lambda start, stop:
                    self.api.products.get_products_with_hits(
                        start=start, stop=stop,
                        augmenter_with_hits=Product.objects.augment_with_hits,
                        **products_args))
            else:
                get_products_range = (lambda start, stop:
                    self.api.products.get_products(start=start, stop=stop,
                                                   **products_args))
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
        start = min(start + 1, total_count)     # humans start counting from 1
        stop = min(stop, total_count)

        pages_count = int(math.ceil(float(total_count)/per_page))
        page_info = lambda number: {
            'name': number,
            'url': self._uri_with_args(base_url, pagina=number),
            'is_current': number == current_page} if number is not None else None
        pages = [page_info(number) for number in self._pages_list(pages_count, current_page)]

        previous_page = page_info(current_page - 1) if current_page > 1 else None
        next_page = page_info(current_page + 1) if current_page < pages_count else None

        data['pagination'] = {'pages': pages,
                              'previous': previous_page,
                              'current': current_page,
                              'next': next_page,
                              'start': start,
                              'stop': stop,
                              'total_count': total_count}
        return data

    def _pages_list(self, pages_count, current_page, max_pages=10):
        return range(1, pages_count + 1)

    def get_products(self):
        products = self.get_products_page().get('products')
        for product in products:
            product_obj = Product(raw=product)
            product['name'] = product_obj.get_short_name()
            product['images'] = product_obj.images
            product['url'] = self._product_url(product)

        products_per_line = 4
        for idx, product in enumerate(products):
            if (idx+1) % products_per_line == 0:
                product['last_in_line'] = True

        return products

    def get_pagination(self):
        return self.get_products_page().get('pagination')

    def get_selectors(self):
        args = self.get_search_args()
        selectors = self.api.categories.get_selectors(
            category_id=args['category_id'],
            selectors_active=args['selectors_active'],
            price_min=args['price_min'], price_max=args['price_max'],
            stock=args['stock'])
        return selectors


class SearchMixin(object):
    def get_context_data(self, **context):
        context.update({'search_form': self.get_search_form})
        return super(SearchMixin, self).get_context_data(**context)

    def get_search_form(self):
        search_in_choices = tuple((c['id'], c['name']) for c in self.api.categories.get_main())
        search_form_class = search_form_factory(search_in_choices, advanced=False)
        search_form = search_form_class(self.request.GET)
        return search_form


class ProductBase(BaseView):
    template_name = "product.html"
    recommended_limit = 3

    def get_local_context(self):
        return {'product': self.get_product(),
                'properties': self.get_properties,
                'recommended': self.get_recommended}

    def get_product(self):
        if not hasattr(self, '_product'):
            product_id = self.kwargs['product_id']
            product_orm = self.api.products.get_and_store(product_id, Product.objects.store)
            if product_orm is None:
                raise Http404()
            product = product_orm.raw
            product['name'] = product_orm.get_best_name()
            product['short_name'] = product_orm.get_short_name()
            product['images'] = product_orm.images()
            product['spec_groups'] = product_orm.get_spec_groups()

            html_template = product_orm.html_description()
            if html_template:
                product_prefix = settings.MEDIA_URL + product_orm.folder_path() + '/'
                context = Context({'PRODUCT_PREFIX': product_prefix})
                product['html_description'] = Template(html_template).render(context)

            product_orm.hit()

            self._product = product
        return self._product

    def get_properties(self):
        items = sorted(self.get_product().get('properties', {}).items())
        return group_in(3, items)

    def get_recommended(self):
        recommended = self.api.products.get_recommended(limit=self.recommended_limit)
        for product in recommended:
            product['images'] = Product(model=product['model']).images
            product['url'] = self._product_url(product)
        return recommended

    def get_breadcrumbs(self):
        product = self.get_product()
        category = self.api.categories.get_category_by_code(product['category_code'])
        if category:
            breadcrumbs = self._get_category_breadcrumbs(category['id'])
            breadcrumbs.append({'name': product['short_name'],
                                'url': None})
        else:
            breadcrumbs = []
        return breadcrumbs


class BrandsBase(BaseView):
    template_name = "branduri.html"
    breadcrumbs = [{'name': "Branduri"}]

    def get_local_context(self):
        return {'brand_index': self._brand_index()}

    def _brand_index(self):
        brands = self.api.products.get_brands()
        index_letters = sorted(set(brand[0].upper() for brand in brands))
        brand_index = dict((letter, sorted(brand for brand in brands
                            if brand[0].upper() == letter))
                           for letter in index_letters)
        grouped_brand_index = grouper(4, sorted(brand_index.items()))
        return grouped_brand_index
