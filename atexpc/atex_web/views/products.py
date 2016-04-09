import math

from django.template import Context, Template
from django.http import Http404, HttpResponseRedirect
from django.conf import settings
from django.core.paginator import Paginator
from django.views.generic.base import TemplateView
from haystack.generic_views import SearchView, FacetedSearchView
from haystack.query import SearchQuerySet
from urllib import urlencode
from urlparse import urlparse, urlunparse, parse_qsl

from atexpc.atex_web.views.base import BreadcrumbsMixin, CSRFCookieMixin, HybridGenericView
from atexpc.atex_web.models import Product, ProductSpecification
from atexpc.atex_web.forms import search_form_factory
from atexpc.atex_web.utils import group_in, grouper
from atexpc.ancora_api.api import Ancora    # STOCK_UNAVAILABLE

import logging
logger = logging.getLogger(__name__)

PRODUCTS_PER_LINE = 4


class HomeView(CSRFCookieMixin, TemplateView):
    template_name = "home.html"
    top_limit = 5

    def get_hits(self):
        hits = []
        # ask for double that we need because some will no longer be available
        product_objects = Product.objects.get_top_hits(limit=self.top_limit * 2)
        product_ids = [p.id for p in product_objects]
        products = self.request.api.products.get_product_list(product_ids)
        for product_obj in product_objects:
            matching_in_backend = [p for p in products
                                   if int(p['id']) == product_obj.id]
            if matching_in_backend:
                product = matching_in_backend[0]
                product['name'] = product_obj.get_short_name()
                product['images'] = product_obj.images
                product['url'] = product_obj.get_absolute_url()
                hits.append(product)
            if len(hits) >= self.top_limit:
                break
        return hits

    def get_recommended(self):
        recommended = self.request.api.products.get_recommended(limit=self.top_limit)
        for product in recommended:
            product_obj = Product(raw=product)
            product['name'] = product_obj.get_short_name()
            product['images'] = product_obj.images
            product['url'] = product_obj.get_absolute_url()
        return recommended

    def get_promotional(self):
        promotional = self.request.api.products.get_promotional(limit=self.top_limit)
        for product in promotional:
            product_obj = Product(raw=product)
            product['name'] = product_obj.get_short_name()
            product['images'] = product_obj.images
            product['url'] = product_obj.get_absolute_url()
        return promotional


class SparsePaginator(Paginator):
    def __init__(self, object_list, per_page, current_page, orphans=0,
                 allow_empty_first_page=True):
        super(SparsePaginator, self).__init__(object_list, per_page, orphans=0,
              allow_empty_first_page=True)
        self.current_page = current_page

    def sparse_page_range(self):
        first_page = 1
        last_page = self.num_pages
        nearby = 5
        min_context = max(first_page, self.current_page - nearby)
        max_context = min(last_page, self.current_page + nearby)
        before, after = [], []
        if min_context == first_page + 1:
            before = [first_page]
        elif min_context >= first_page + 2:
            before = [first_page, None]
        if max_context <= last_page - 2:
            after = [None, last_page]
        elif max_context <= last_page - 1:
            after = [last_page]
        pages = before + range(min_context, max_context + 1) + after
        return pages


class MySearchView(CSRFCookieMixin, SearchView):
    template_name = "search.html"
    form_name = "filter_form"
    search_field = "q"
    page_kwarg = "pagina"

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates a blank version of the form.
        """
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            response = self.form_valid(form)
            if self.queryset.count() == 1:
                return HttpResponseRedirect(self.queryset[0].object.get_absolute_url())
            else:
                return response
        else:
            return self.form_invalid(form)

    def get_form_class(self):
        search_in_choices = tuple((c['code'], c['name']) for c in self.request.api.categories.get_main())
        return search_form_factory(search_in_choices, advanced=True)

    def get_paginate_by(self, queryset):
        return self.request.GET.get("pe_pagina", 20)

    def get_paginator(self, queryset, per_page, orphans=0,
                      allow_empty_first_page=True, **kwargs):
        current_page = int(self.request.GET.get(self.page_kwarg, 1))
        return SparsePaginator(
            queryset, per_page, current_page=current_page, orphans=orphans,
            allow_empty_first_page=allow_empty_first_page, **kwargs)

    # def get_queryset(self):
    #     queryset = super(MySearchView, self).get_queryset()
    #     # further filter queryset based on some set of criteria
    #     return queryset.filter(pub_date__gte=date(2015, 1, 1))

    def get_context_data(self, **kwargs):
        context = super(MySearchView, self).get_context_data(**kwargs)
        products = [result.object for result in context['object_list'] if result.object]

        # TODO: refactor as it's the same in ProductsView
        for idx, product in enumerate(products):
            if (idx+1) % PRODUCTS_PER_LINE == 0:
                setattr(product, 'last_in_line', True)

        self.augment_products(products)
        context['object_list'] = products
        if not products:
            context['no_products'] = self.get_no_products_message(context[self.form_name])
        context['search_url'] = _uri_with_args(self.request.build_absolute_uri(), page=None)
        # context['facets'] = context['object_list'].facet_counts()
        return context

    def get_no_products_message(self, form):
        keywords = form.cleaned_data[self.search_field]
        message = 'Nu am gasit produse "%s"' % (keywords,)

        category_code = form.cleaned_data['cauta_in']
        category = self.request.api.categories.get_category_by_code(str(category_code)) if category_code else None
        if category:
            message += ' din categoria "%s"' % (category['name'],)

        in_stock = form.cleaned_data['stoc']
        if in_stock:
            message += ', in stoc'

        return message + '!'

    def augment_products(self, products):
        """ Augments products from search with updated info from Ancora """
        product_ids = [p.id for p in products]
        products_ancora = self.request.api.products.get_product_list(product_ids)
        for product in products:
            ancora_product = [p for p in products_ancora if product.id == p['id']]
            ancora_product = ancora_product[0] if ancora_product else {}
            setattr(product, 'price', ancora_product.get('price'))
            setattr(product, 'old_price', ancora_product.get('old_price'))
            setattr(product, 'stock_info', ancora_product.get('stock_info'))
            setattr(product, 'stock_available', ancora_product.get('stock_status') != Ancora.STOCK_UNAVAILABLE)
        return products


class SearchAutoComplete(HybridGenericView):
    json_exclude = ('view',)
    def get_context_data(self, **kwargs):
        context = super(SearchAutoComplete, self).get_context_data(**kwargs)

        sqs = SearchQuerySet().autocomplete(name_auto=self.request.GET.get('q', '')) \
                              .order_by('-hits')[:10]
        context['suggestions'] = [result.name_auto for result in sqs]

        return context


class ProductsView(BreadcrumbsMixin, CSRFCookieMixin, TemplateView):
    template_name = "products.html"

    def get_context_data(self, **context):
        context.update({'filter_form': self.get_search_form,
                        'selectors': self.get_selectors,
                        'selectors_active': lambda: self.get_search_args()['selectors_active'],
                        'price_min': lambda: self.get_search_args()['price_min'],
                        'price_max': lambda: self.get_search_args()['price_max'],
                        'products': self.get_products(),
                        'pagination': self.get_pagination})
        return super(ProductsView, self).get_context_data(**context)

    def get_breadcrumbs(self):
        args = self.get_search_args()
        return self._get_search_breadcrumbs(args['keywords'], args['category_id'], args['selectors_active'])

    def get_search_form(self):
        if not hasattr(self, '_search_form'):
            request_GET = self.request.GET.copy()
            if request_GET.get('categorie') is None:
                request_GET['categorie'] = self.get_category_id()
            search_in_choices = tuple((c['code'], c['name']) for c in self.request.api.categories.get_main())
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
            args['keywords'] = search_form.cleaned_data.get('q')
            args['base_category'] = search_form.cleaned_data.get('cauta_in')
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
        if self.request.GET.get('q'):
            category_id = None  # search in base category, not specific category
        else:
            category_id = self.kwargs.get('category_id') or self.request.GET.get('categorie')
        return int(category_id) if category_id else None

    def get_products_page(self):
        if not hasattr(self, '_products_page'):
            args = self.get_search_args()
            products_args = {
                'category_id': args['category_id'],
                'keywords': args['keywords'], 'base_category': args['base_category'],
                'selectors': args['selectors_active'], 'price_min': args['price_min'],
                'price_max': args['price_max'], 'stock': args['stock'],
                'sort_by': args['sort_by'], 'sort_order': args['sort_order']}
            if args['sort_by'] == "vanzari":
                get_products_range = (lambda start, stop:
                    self.request.api.products.get_products_with_hits(
                        start=start, stop=stop,
                        augmenter_with_hits=Product.objects.augment_with_hits,
                        **products_args))
            else:
                get_products_range = (lambda start, stop:
                    self.request.api.products.get_products(start=start, stop=stop,
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
            'url': _uri_with_args(base_url, pagina=number),
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

    def _pages_list(self, pages_count, current_page, nearby=5):
        first_page = 1
        last_page = pages_count
        min_context = max(first_page, current_page - nearby)
        max_context = min(last_page, current_page + nearby)
        before, after = [], []
        if min_context == first_page + 1:
            before = [first_page]
        elif min_context >= first_page + 2:
            before = [first_page, None]
        if max_context <= last_page - 2:
            after = [None, last_page]
        elif max_context <= last_page - 1:
            after = [last_page]
        pages = before + range(min_context, max_context + 1) + after
        return pages

    def get_products(self):
        products = self.get_products_page().get('products')
        for product in products:
            product_obj = Product(raw=product)
            product['name'] = product_obj.get_short_name()
            product['images'] = product_obj.images
            product['url'] = product_obj.get_absolute_url()
            product['stock_available'] = product['stock_status'] != Ancora.STOCK_UNAVAILABLE

        for idx, product in enumerate(products):
            if (idx+1) % PRODUCTS_PER_LINE == 0:
                product['last_in_line'] = True

        return products

    def get_pagination(self):
        return self.get_products_page().get('pagination')

    def get_selectors(self):
        args = self.get_search_args()
        selectors = self.request.api.categories.get_selectors(
            category_id=args['category_id'],
            selectors_active=args['selectors_active'],
            price_min=args['price_min'], price_max=args['price_max'],
            stock=args['stock'])
        selectors_with_products = [{'name': group['name'],
                                    'selectors': [selector for selector in group['selectors'] if selector['count'] > 0]}
                                   for group in selectors] # if len(group['selectors']) > 0]
        return selectors_with_products


class ProductView(BreadcrumbsMixin, CSRFCookieMixin, TemplateView):
    template_name = "product.html"
    recommended_limit = 3

    def get_context_data(self, **context):
        context.update({'product': self.get_product(),
                        'properties': self.get_properties,
                        'recommended': self.get_recommended})
        return super(ProductView, self).get_context_data(**context)

    def get_product(self):
        if not hasattr(self, '_product'):
            product_id = self.kwargs['product_id']
            product_orm = self.request.api.products.get_and_store(product_id, Product.objects.store)
            if product_orm is None:
                raise Http404()
            product = product_orm.raw
            product['name'] = product_orm.get_best_name()
            product['short_name'] = product_orm.get_short_name()
            product['images'] = product_orm.images()
            product['spec_groups'] = product_orm.get_spec_groups()
            product['stock_available'] = product['stock_status'] != Ancora.STOCK_UNAVAILABLE

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
        recommended = self.request.api.products.get_recommended(limit=self.recommended_limit)
        for product in recommended:
            product_obj = Product(raw=product)
            product['name'] = product_obj.get_short_name()
            product['images'] = product_obj.images
            product['url'] = product_obj.get_absolute_url()
        return recommended

    def get_breadcrumbs(self):
        product = self.get_product()
        category = self.request.api.categories.get_category_by_code(product['category_code'])
        if category:
            breadcrumbs = self._get_category_breadcrumbs(category['id'])
            breadcrumbs.append({'name': product['short_name'],
                                'url': None})
        else:
            breadcrumbs = []
        return breadcrumbs


class BrandsView(BreadcrumbsMixin, TemplateView):
    template_name = "branduri.html"
    breadcrumbs = [{'name': "Branduri"}]


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
