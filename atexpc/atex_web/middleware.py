from operator import itemgetter

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
import logging

from atexpc.atex_web.ancora_api import AncoraAPI
from atexpc.atex_web.forms import search_form_factory
from atexpc.atex_web.models import Category
from atexpc.atex_web.views.shopping import get_cart_data

logger = logging.getLogger(__name__)


class AncoraMiddleware:
    def process_request(self, request):
        request.api = AncoraAPI()
        return None

    def process_template_response(self, request, response):
        if hasattr(response, 'context_data'):
            response.context_data['search_form'] = get_search_form(request)
        return response

    def process_exception(self, request, exception):
        # self.api = AncoraAPI(use_backend=False)
        return None   # or HttpResponse() if it's an APIError

def context_processor(request):
    return {'menu': get_menu(request.api),
            'categories': request.api.categories.get_main,
            'site_info': get_site_info(request),
            'cart': get_cart_data(request)}

def get_menu(api):
    def category_icon(category):
        icons = {'1': 'images/desktop-icon.png',
                 '2': 'images/tv-icon.png',
                 '3': 'images/hdd-icon.png',
                 '4': 'images/mouse-icon.png',
                 '5': 'images/printer-icon.png',
                 '6': 'images/network-icon.png',
                 '7': 'images/cd-icon.png',
                 '8': 'images/phone-icon.png',
                 '9': 'images/conectica-icon.png',
                 '99': 'images/camera-icon.png',
                 '999': 'images/gopro-icon.png'}
        return icons.get(category['code'], '')

    def category_background_class(category):
        try:
            background_class = "bg-%02d" % int(category['code'])
        except ValueError:
            background_class = ""
        return background_class

    def categories_in(category=None):
        parent_id = category['code'] if category is not None else None
        categories = api.categories.get_children(parent_id)
        sorted_categories = sorted(categories, key=itemgetter('code'))
        return sorted_categories

    def menu_category(category):
        """Prepare a category to be displayed in the menu"""
        menu_category = {'name': category['name'],
                         'url': _category_url(category),
                         'count': category['count'],
                         'level': _category_level(category)}
        return menu_category

    def insert_in_column_grouped(submenu_items, columns, max_per_column):
        """ Insert all into the first column with enough space """
        inserted = False
        for column in columns:
            if len(column) + len(submenu_items) <= max_per_column:
                column.extend(submenu_items)
                inserted = True
                break
        return columns, inserted

    def insert_in_column_anyway(submenu_items, columns, max_per_column):
        """ Insert partially into any column with enough space """
        for column in columns:
            can_insert = max_per_column - len(column)
            enough_to_fill = len(submenu_items) >= can_insert
            if can_insert > 0:
                removed, submenu_items = submenu_items[:can_insert], submenu_items[can_insert:]
                column.extend(removed)
        inserted = len(submenu_items) == 0
        return columns, inserted

    menu = []
    max_per_column = 10
    for top_category in categories_in(None):
        columns = [[], [], []]
        for level2_category in categories_in(top_category):
            submenu_items = ([menu_category(level2_category)] +
                             [menu_category(level3_category)
                              for level3_category in categories_in(level2_category)])
            columns, inserted = insert_in_column_grouped(submenu_items, columns, max_per_column)
            if not inserted:
                columns, inserted = insert_in_column_anyway(submenu_items, columns, max_per_column)
            if not inserted:
                logger.debug("Too many subcategories in %s", top_category['code'])

        category = menu_category(top_category)
        category.update({'columns': columns,
                         'icon': category_icon(top_category),
                         'background_class': category_background_class(top_category)})
        menu.append(category)

    return menu

def get_search_form(request):
    search_in_choices = tuple((c['code'], c['name']) for c in request.api.categories.get_main())
    search_form_class = search_form_factory(search_in_choices, advanced=False)
    search_form = search_form_class(request.GET)
    return search_form

def get_site_info(request):
    current_site = get_current_site(request)
    base_domain = get_base_domain(request)
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

def get_base_domain(request):
    """Get the last 2 segments of the domain name"""
    domain = get_current_site(request).domain
    return '.'.join(domain.split('.')[-2:])

def _category_url(category):
    return Category(id=category['id'], name=category['name']).get_absolute_url()

def _category_level(category):
    return category['code'].count('.') + 1

