import re
import json
from operator import itemgetter

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.text import slugify
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.contrib.sites.models import get_current_site
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from atexpc.ancora_api.api import APIError
from atexpc.atex_web.ancora_api import AncoraAPI
from atexpc.atex_web.models import Product

import logging
logger = logging.getLogger(__name__)


class BaseView(TemplateView):
    def __init__(self, *args, **kwargs):
        super(BaseView, self).__init__(*args, **kwargs)
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

    def get_local_context(self):
        return {}

    def get_context_data(self, **context):
        context.update(self.get_general_context())
        context.update(self.get_local_context())
        return super(BaseView, self).get_context_data(**context)

    def get(self, request, *args, **kwargs):
        try:
            response = super(BaseView, self).get(request, *args, **kwargs)
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
                     '8': 'images/phone-icon.png',
                     '9': 'images/conectica-icon.png'}
            return icons.get(category['code'], '')

        def category_background_class(category):
            try:
                background_class = "bg-%02d" % int(category['code'])
            except ValueError:
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
                             'url': self._category_url(category),
                             'count': category['count'],
                             'level': self._category_level(category)}
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

    def get_footer(self):
        return [{'name': category['name'],
                 'url': self._category_url(category)}
                for category in self.api.categories.get_all()
                if self._category_level(category) >= 2 and category['count'] > 0]

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

    def _category_url(self, category):
        return reverse('category', kwargs={'category_id': category['id'],
                                           'slug': slugify(category['name'])})

    def _category_level(self, category):
        return category['code'].count('.') + 1

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, *args, **kwargs):
        return super(BaseView, self).dispatch(*args, **kwargs)


class ErrorBase(BaseView):
    error_code = None

    def get_template_names(self):
        return "%d.html" % self.error_code

    def render_to_response(self, context):
        response = super(ErrorBase, self).render_to_response(context)
        response.status_code = self.error_code
        response.render()   # response is not yet rendered during middleware
        return response

    def get_breadcrumbs(self):
        return [{'name': "Pagina necunoscuta"}]


class BreadcrumbsMixin(object):
    def get_context_data(self, **context):
        context.update({'breadcrumbs': self.get_breadcrumbs})
        return super(BreadcrumbsMixin, self).get_context_data(**context)

    def get_breadcrumbs(self):
        if hasattr(super(BreadcrumbsMixin, self), 'get_breadcrumbs'):
            breadcrumbs = super(BreadcrumbsMixin, self).get_breadcrumbs()
        else:
            breadcrumbs = getattr(self, 'breadcrumbs', [])
        if breadcrumbs and 'url' in breadcrumbs[-1]:
            breadcrumbs[-1] = breadcrumbs[-1].copy()
            breadcrumbs[-1]['url'] = None   # the current navigation item is not clickable
        return breadcrumbs

    def _get_search_breadcrumbs(self, search_keywords, category_id, selectors):
        breadcrumbs = []
        if search_keywords:
            breadcrumbs.append({'name': '"%s"' % search_keywords,
                                'url': None})
        elif category_id:
            breadcrumbs = self._get_category_breadcrumbs(category_id)
        elif selectors:
            breadcrumbs.append({'name': ", ".join(selectors),
                                'url': None})
        return breadcrumbs

    def _get_category_breadcrumbs(self, category_id):
        breadcrumbs = []
        category = self.request.api.categories.get_category(category_id)
        while category is not None:
            crumb = {'name': category['name'],
                     'url': self._category_url(category) if category.get('count') else None}
            breadcrumbs.insert(0, crumb)
            category = self.request.api.categories.get_parent_category(category['id'])
        return breadcrumbs

    def _category_url(self, category):
        return reverse('category', kwargs={'category_id': category['id'],
                                           'slug': slugify(category['name'])})


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
        def none_unless_serializable(obj):
            if type(obj) not in (str, unicode, int, long, float, bool, None):
                return None
            return obj

        json_exclude = getattr(self, 'json_exclude', ())
        json_context = dict((k, v) for k, v in context.items() if k not in json_exclude)
        return json.dumps(json_context, skipkeys=True, default=none_unless_serializable)


class HybridGenericView(JSONResponseMixin, BaseView):
    def render_to_response(self, context):
        if self.request.is_ajax() or self.template_name is None:
            return JSONResponseMixin.render_to_response(self, context)
        else:
            return BaseView.render_to_response(self, context)
