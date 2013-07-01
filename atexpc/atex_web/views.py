import re
import math
import json
from operator import itemgetter
from itertools import groupby
from urlparse import urlparse, urlunparse, parse_qsl
from urllib import urlencode

from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth import authenticate, login
from django.utils.text import slugify
from django.template import Context, Template
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.sites.models import get_current_site
from django.http import Http404
from django.conf import settings

from models import Product, DatabaseCart as Cart
from forms import search_form_factory, user_form_factory
from atexpc.ancora_api.api import APIError
from ancora_api import AncoraAPI

import logging
logger = logging.getLogger(__name__)


class GenericView(TemplateView):
    def __init__(self, *args, **kwargs):
        super(GenericView, self).__init__(*args, **kwargs)
        self.api = AncoraAPI()

    def get_general_context(self):
        return {'menu': self.get_menu,
                'categories': self.api.categories.get_main,
                'footer': self.get_footer,
                'site_info': self.get_site_info}

    def get_minimal_context(self):
        self.api = AncoraAPI(use_backend=False)
        return {'menu': self.get_menu(),
                'categories': self.api.categories.get_main(),
                'footer': self.get_footer(),
                'site_info': self.get_site_info()}

    def get_particular_context(self):
        return {}

    def get_context_data(self, **kwargs):
        context = super(GenericView, self).get_context_data(**kwargs)
        context.update(self.get_general_context())
        context.update(self.get_particular_context())
        return context

    def get(self, request, *args, **kwargs):
        try:
            response = super(GenericView, self).get(request, *args, **kwargs)
        except APIError as e:
            logger.error(e, extra={'request': self.request})
            context = self.get_minimal_context()
            context['error'] = e
            response = self.render_to_response(context)
        return response

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
            categories = self.api.categories.get_children(parent_id)
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
                for category in self.api.categories.get_all()
                if _category_level(category) >= 2 and category['count'] > 0]

    def get_site_info(self):
        current_site = get_current_site(self.request)
        base_domain = self._get_base_domain()
        company_name = {
            'atexpc.ro': "ATEX Computer SRL",
            'atexsolutions.ro': "ATEX Solutions SRL-D",
            'nul.ro': "ATEX Computer SRL"
        }
        site_info = {
            'name': current_site.name,
            'domain': current_site.domain,
            'company': company_name.get(base_domain, current_site.name),
            'logo_url': "%simages/logo-%s.png" % (settings.STATIC_URL, base_domain)
        }
        return site_info

    def _get_base_domain(self):
        """Get the last 2 segments of the domain name"""
        domain = get_current_site(self.request).domain
        return '.'.join(domain.split('.')[-2:])

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, *args, **kwargs):
        return super(GenericView, self).dispatch(*args, **kwargs)

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
        category = self.api.categories.get_category(category_id)
        while category is not None:
            crumb = {'name': category['name'],
                     'url': _category_url(category)}
            breadcrumbs.insert(0, crumb)
            category = self.api.categories.get_parent_category(category['id'])
        return breadcrumbs


class SearchMixin(object):
    def get_context_data(self, **kwargs):
        context = super(SearchMixin, self).get_context_data(**kwargs)
        context.update({'search_form': self.get_search_form})
        return context

    def get_search_form(self):
        search_in_choices = tuple((c['id'], c['name']) for c in self.api.categories.get_main())
        search_form_class = search_form_factory(search_in_choices, advanced=False)
        search_form = search_form_class(self.request.GET)
        return search_form


class ShoppingMixin(object):
    def get_context_data(self, **kwargs):
        context = super(ShoppingMixin, self).get_context_data(**kwargs)
        context.update({'cart': self._get_cart_data()})
        return context

    def _get_cart(self):
        cart_id = self.request.session.get('cart_id')
        cart = Cart.get(cart_id) if cart_id else None
        return cart

    def _create_cart(self):
        # TODO: are cookies enabled ?
        self.request.session.save()
        session_id = self.request.session.session_key
        cart = Cart.create(session_id)
        self.request.session['cart_id'] = cart.id()
        return cart

    def _get_cart_data(self):
        cart = self._get_cart()
        if cart:
            cart_data = {'id': cart.id(),
                         'items': cart.items(),
                         'count': cart.count(),
                         'price': cart.price()}
        else:
            cart_data = {'id': None, 'items': [], 'count': 0, 'price': 0.0}
        return cart_data

    def _add_to_cart(self, product_id):
        cart = self._get_cart()
        if cart is None:
            cart = self._create_cart()
        cart.add_item(product_id)


class JSONResponseMixin(object):
    """A mixin that can be used to render a JSON response."""

    def render_to_response(self, context, **response_kwargs):
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(
            self.convert_context_to_json(context),
            **response_kwargs
        )

    def convert_context_to_json(self, context):
        """Naive conversion of the context dictionary into a JSON object"""
        return json.dumps(context)


class HybridGenericView(JSONResponseMixin, GenericView):
    def render_to_response(self, context):
        if self.request.is_ajax():
            return JSONResponseMixin.render_to_response(self, context)
        else:
            return GenericView.render_to_response(self, context)


class CartView(ShoppingMixin, SearchMixin, HybridGenericView):
    template_name = "cart.html"

    def get_json_context(self):
        return {'cart': self._get_cart_data()}

    def post(self, request, *args, **kwargs):
        method = request.POST.get('method')
        product_id = request.POST.get('product_id')
        if method == 'add':
            self._add_to_cart(product_id)
        return self.render_to_response(self.get_json_context())


class OrderView(FormView, ShoppingMixin, SearchMixin, HybridGenericView):
    template_name = "order.html"
    success_url = reverse_lazy('confirm')

    def get_form_class(self):
        logintype = self.request.POST.get('logintype', None)
        return user_form_factory(logintype)

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        logger.debug("OrderView.form_valid %s %s", form.is_valid(), form.cleaned_data)
        if form.cleaned_data['logintype'] == 'new':
            result = self.api.users.create_user(
                email=form.cleaned_data['email'],
                fname=form.cleaned_data['firstname'],
                lname=form.cleaned_data['surname'],
                password=form.cleaned_data['password1'],
                usertype=form.cleaned_data['usertype'])
            logger.info('Signup %s', result)
        elif form.cleaned_data['logintype'] == 'old':
            user = authenticate(email=form.cleaned_data['user'],
                                password=form.cleaned_data['password'])
            if user is not None:    # user.is_active ?
                login(self.request, user)
                logger.info('Login %s', user.email)
        return super(OrderView, self).form_valid(form)

    def form_invalid(self, form):
        logger.debug("OrderView.form_invalid" + str(form.errors))
        return super(OrderView, self).form_valid(form)

class ConfirmView(ShoppingMixin, SearchMixin, HybridGenericView):
    template_name = "confirm.html"


class HomeView(ShoppingMixin, SearchMixin, GenericView):
    template_name = "home.html"
    top_limit = 5

    def get_particular_context(self):
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
                product['name'] = product_obj.get_best_name()
                product['images'] = product_obj.images
                product['url'] = _product_url(product)
                hits.append(product)
        return hits
    
    def get_recommended(self):
        recommended = self.api.products.get_recommended(limit=self.top_limit)
        for product in recommended:
            product_obj = Product(raw=product)
            product['name'] = product_obj.get_best_name()
            product['images'] = product_obj.images
            product['url'] = _product_url(product)
        return recommended

    def get_promotional(self):
        promotional = self.api.products.get_promotional(limit=self.top_limit)
        for product in promotional:
            product_obj = Product(raw=product)
            product['name'] = product_obj.get_best_name()
            product['images'] = product_obj.images
            product['url'] = _product_url(product)
        return promotional


class SearchView(ShoppingMixin, BreadcrumbsMixin, GenericView):
    template_name = "search.html"

    def get_particular_context(self):
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
        return self.kwargs.get('category_id') or self.request.GET.get('categorie')

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
            product_obj = Product(raw=product)
            product['name'] = product_obj.get_best_name()
            product['images'] = product_obj.images
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
        selectors = self.api.categories.get_selectors(
            category_id=args['category_id'], 
            selectors_active=args['selectors_active'],
            price_min=args['price_min'], price_max=args['price_max'])
        return selectors

class ProductView(ShoppingMixin, SearchMixin, BreadcrumbsMixin, GenericView):
    template_name = "product.html"
    recommended_limit = 3

    def get_particular_context(self):
        return {'product': self.get_product(),
                'properties': self.get_properties,
                'recommended': self.get_recommended}

    def get_product(self):
        if not hasattr(self, '_product'):
            product_id = self.kwargs['product_id']
            product_obj = self.api.products.get_and_store(product_id, Product.objects.store)
            if product_obj is None:
                raise Http404()
            product = product_obj.raw
            product['name'] = product_obj.get_best_name()
            product['images'] = product_obj.images()
            html_template = product_obj.html_description()
            if html_template:
                product_prefix = settings.MEDIA_URL + product_obj.folder_path() + '/'
                context = Context({'PRODUCT_PREFIX': product_prefix})
                product['html_description'] = Template(html_template).render(context)

            product_obj.hit()

            self._product = product
        return self._product

    def get_properties(self):
        items = sorted(self.get_product().get('properties', {}).items())
        def group_in(n):
            return [[item for i, item in group] for i, group
                    in groupby(sorted((i%n, item) for i, item 
                                      in enumerate(items)),
                               itemgetter(0))]
        return group_in(3)

    def get_recommended(self):
        recommended = self.api.products.get_recommended(limit=self.recommended_limit)
        for product in recommended:
            product['images'] = Product(model=product['model']).images
            product['url'] = _product_url(product)
        return recommended

    def get_breadcrumbs(self):
        product = self.get_product()
        category = self.api.categories.get_category_by_code(product['category_code'])
        if category:
            breadcrumbs = self._get_category_breadcrumbs(category['id'])
            breadcrumbs.append({'name': product['name'],
                                'url': None})
        else:
            breadcrumbs = []
        return breadcrumbs


class ContactView(ShoppingMixin, BreadcrumbsMixin, SearchMixin, GenericView):
    def get_template_names(self):
        return "contact-%s.html" % self._get_base_domain()

    def get_breadcrumbs(self):
        return [{'name': "Contact"}]


class ConditionsView(BreadcrumbsMixin, SearchMixin, GenericView):
    template_name = "conditions.html"

    def get_breadcrumbs(self):
        return [{'name': "Conditii Vanzare"}]


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


class ErrorView(BreadcrumbsMixin, SearchMixin, GenericView):
    error_code = None

    def get_template_names(self):
        return "%d.html" % self.error_code

    def render_to_response(self, context):
        response = super(ErrorView, self).render_to_response(context)
        response.status_code = self.error_code
        response.render() # response is not yet rendered during middleware
        return response

    def get_breadcrumbs(self):
        return [{'name': "Pagina necunoscuta"}]


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
