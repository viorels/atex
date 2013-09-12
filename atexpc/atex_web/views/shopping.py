from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth import login
from django.views.generic.edit import FormView
import requests

from atexpc.atex_web.forms import order_form_factory
from atexpc.atex_web.views.base import HybridGenericView
from atexpc.atex_web.models import CartFactory
from atexpc.atex_web.utils import LoginRequiredMixin, FrozenDict
from atexpc.atex_web.templatetags import atex_tags

import logging
logger = logging.getLogger(__name__)


class CartBase(HybridGenericView):
    template_name = "cart.html"
    breadcrumbs = [FrozenDict(name="Cos cumparaturi",
                              url=reverse_lazy('cart'))]

    def get_json_context(self):
        return {'cart': self._get_cart_data()}

    def post(self, request, *args, **kwargs):
        method = request.POST.get('method')
        if method == 'add':
            product_id = int(request.POST.get('product_id'))
            self._add_to_cart(product_id)
        elif method == 'update':
            products_count = {}
            for key, value in request.POST.iteritems():
                if key.startswith('product_'):
                    product_id = int(key.lstrip('product_').rstrip('_count'))
                    count = int(value)
                    products_count[product_id] = count
            self._update_cart(products_count)
        if request.POST.get('next'):
            request.session['delivery'] = request.POST.get('delivery')
            request.session['payment'] = request.POST.get('payment')
            return HttpResponseRedirect(reverse('order'))
        return self.render_to_response(self.get_json_context())


class OrderBase(LoginRequiredMixin, FormView, HybridGenericView):
    template_name = "order.html"
    breadcrumbs = CartBase.breadcrumbs + [FrozenDict(name="Date facturare",
                                                     url=reverse_lazy('order'))]
    success_url = reverse_lazy('confirm')

    def get_context_data(self, **kwargs):
        context = super(OrderBase, self).get_context_data(**kwargs)
        if 'form' not in context:   # show full unbound form on first view
            context['form'] = self.get_form_class()()
        return context

    def get_form_class(self):
        customer_type = self.request.POST.get('customer_type')
        logger.debug('order form %s' % customer_type)
        return order_form_factory(customer_type)

    def form_valid(self, form):
        logger.info('Order %s', form.cleaned_data)
        self.request.session['order'] = form.cleaned_data
        return super(OrderBase, self).form_valid(form)

    def form_invalid(self, form):
        logger.info('Order errors %s', form.errors)
        return super(OrderBase, self).form_invalid(form)

class GetCompanyInfo(HybridGenericView):
    """ Get company info by CIF from openapi.ro """

    template_name = None
    json_exclude = ('object_list', 'view', 'paginator', 'page_obj', 'is_paginated')

    def get_local_context(self):
        cif = self.kwargs.get('cif')
        r = requests.get('http://openapi.ro/api/companies/%s.json' % cif)
        return r.json


class ConfirmBase(LoginRequiredMixin, HybridGenericView):
    template_name = "confirm.html"
    breadcrumbs = OrderBase.breadcrumbs + [FrozenDict(name="Confirmare",
                                                      url=reverse_lazy('confirm'))]

    def get_local_context(self):
        return {'order': self.request.session.get('order')}

    def post(self, request, *args, **kwargs):
        cart_id = self._get_cart_data()['id']
        ancora_user_id = self.request.user.get_ancora_id(self.api)
        order_info = request.session.get('order')
        new_order = dict(cart_id=cart_id,
                         user_id=ancora_user_id,
                         email=request.user.email,
                         customer_type=order_info['customer_type'],
                         name=order_info['last_name'] + order_info['first_name'],
                         tax_code=order_info['cnp'],
                         phone=order_info['phone'],
                         address=order_info['address'],
                         city=order_info['city'],
                         county=order_info['county'])
        logger.info('Confirm %s', new_order)
        cart = self._get_cart_data()
        logger.debug("Cart %s", cart)
        order_info['id'] = self.api.cart.create_order(**new_order)
        del request.session['cart_id']  # Ancora cart is deleted after order
        return self.get(request, cart=cart, order=order_info, done=True)


class ShoppingMixin(object):
    def get_context_data(self, **context):
        if 'cart' not in context:
            context.update({'cart': self._get_cart_data()})
        return super(ShoppingMixin, self).get_context_data(**context)

    def _get_cart(self):
        cart_id = self.request.session.get('cart_id')
        cart = CartFactory(api=self.api).get(cart_id) if cart_id else None
        return cart

    def _create_cart(self):
        # TODO: are cookies enabled ?
        ancora_user_id = guest_id = 0
        if self.request.user.is_authenticated():
            ancora_user_id = self.request.user.get_ancora_id(self.api)
        cart = CartFactory(api=self.api).create(ancora_user_id)
        self.request.session['cart_id'] = cart.id()
        return cart

    def _get_cart_data(self):
        cart = self._get_cart()
        if cart:
            items = self._augment_cart_items(cart.items())
            cart_data = {'id': cart.id(),
                         'items': items,
                         'count': sum(item['count'] for item in items),
                         'price': cart.price(items) + cart.delivery_price(items),
                         'delivery_price': cart.delivery_price(items)}
        else:
            cart_data = {'id': None, 'items': [], 'count': 0, 'price': 0.0}
        return cart_data

    def _augment_cart_items(self, items):
        for item in items:
            product = item['product']
            api_product = self.api.products.get_product(product['id'])
            product.update({'description': api_product['description'],
                            'price': api_product['price'],
                            'stock_info': api_product['stock_info'],
                            'warranty': api_product['warranty'],
                            'url': self._product_url(product),
                            'thumb_80x80_url': atex_tags.thumbnail(product['images'][0], '80x80')})
            del product['images']   # not serializable
            item['price'] = item['count'] * product['price']
        return items

    def _add_to_cart(self, product_id):
        cart = self._get_cart()
        if cart is None:
            cart = self._create_cart()
        cart.add_item(product_id)

    def _update_cart(self, products={}):
        """ Update produt count or delete products from cart.
            Argument is a dict with id: count items """
        cart = self._get_cart()
        if cart:
            for item in cart.items():
                product_id = item['product']['id']
                if product_id in products:
                    count = products[product_id]
                    cart.update_item(product_id, count)
                else:
                    cart.remove_item(product_id)
