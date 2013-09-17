from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth import login
from django.views.generic.edit import FormView
from localflavor.ro.ro_counties import COUNTIES_CHOICES
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
        next_step = request.POST.get('next')
        if method == 'add':
            product_id = int(request.POST.get('product_id'))
            self._add_to_cart(product_id)
        if method == 'delivery':
            self._update_cart_options(delivery=request.POST.get('delivery'))
        elif method == 'update' or next_step:
            products_count = {}
            for key, value in request.POST.iteritems():
                if key.startswith('product_'):
                    product_id = int(key.lstrip('product_').rstrip('_count'))
                    count = int(value)
                    products_count[product_id] = count
            self._update_cart(products_count)
            self._update_cart_options(delivery=request.POST.get('delivery'),
                                      payment=request.POST.get('payment'))

        if next_step:
            return HttpResponseRedirect(reverse('order'))
        else:
            return self.render_to_response(self.get_json_context())


class OrderBase(LoginRequiredMixin, FormView, HybridGenericView):
    template_name = "order.html"
    breadcrumbs = CartBase.breadcrumbs + [FrozenDict(name="Date facturare",
                                                     url=reverse_lazy('order'))]
    success_url = reverse_lazy('confirm')

    def get_context_data(self, **kwargs):
        context = super(OrderBase, self).get_context_data(**kwargs)
        if 'form' not in context:   # show full unbound form on first view
            context['form'] = self.get_form_class()
        context['customers'] = self.api.cart.get_customers(user_id=self.request.user.ancora_id)
        context['counties'] = [county for short, county in COUNTIES_CHOICES]
        return context

    def get_form_class(self):
        customer_type = self.request.POST.get('customer_type')
        user = self.request.user
        customers = self.api.cart.get_customers(user_id=user.ancora_id)
        delivery = self.request.session.get('delivery') == 'yes'
        return order_form_factory(form_type=customer_type, 
                                  user=user,
                                  customers=customers,
                                  delivery=delivery)

    def form_valid(self, form):
        logger.info('Order %s', form.cleaned_data)
        self.request.session['order'] = form.cleaned_data

        # Update user
        self.request.user.first_name = form.cleaned_data['first_name']
        self.request.user.last_name = form.cleaned_data['last_name']
        self.request.user.phone = form.cleaned_data['phone']
        self.request.user.save()

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
        order_info = request.session.get('order').copy()
        cart = self._get_cart_data()
        cart_id = cart['id']
        if cart_id is None:
            return HttpResponseRedirect(reverse('cart'))
        ancora_user_id = self.request.user.get_ancora_id(self.api)
        customer_type = order_info['customer_type']
        person_name = "%s %s" % (order_info['first_name'], order_info['last_name'])
        tax_code_type = {'f': 'cnp', 'j': 'cui', 'o': 'cif'}
        tax_code = order_info[tax_code_type[customer_type]]
        if order_info['delivery'] == 'same':
            order_info['delivery_county'] = order_info['county']
            order_info['delivery_city'] = order_info['city']
            order_info['delivery_address'] = order_info['address'] 
        order_info.update(cart_id=cart_id,
                          user_id=ancora_user_id,
                          email=order_info['username'],
                          name=(person_name if customer_type == 'f' else order_info['company']),
                          person_name=person_name,
                          delivery=order_info['delivery'] in ('same', 'other'),
                          tax_code=tax_code)
        logger.info('Confirm %s, cart %s', order_info, cart)
        order_id = self.api.cart.create_order(**order_info)
        request.session['order']['id'] = order_id
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
        delivery = self.request.session.get('delivery', 'no') != 'no'
        payment = self.request.session.get('payment', 'cash')
        if cart:
            items = self._augment_cart_items(cart.items())
            delivery_price = cart.delivery_price(delivery=delivery,
                                                 cash_payment=(payment == 'cash'))
            cart_data = {'id': cart.id(),
                         'items': items,
                         'count': sum(item['count'] for item in items),
                         'price': cart.price(items) + delivery_price,
                         'delivery_price': delivery_price}
        else:
            cart_data = {'id': None, 'items': [], 'count': 0, 'price': 0.0}
 
        cart_data['delivery'] = delivery
        cart_data['payment'] = payment
        cart_data.update(self._cart_options_description(delivery=delivery, payment=payment))

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

    def _update_cart_options(self, delivery, payment=None):
        self.request.session['delivery'] = delivery
        if payment is not None:
            self.request.session['payment'] = payment

    def _cart_options_description(self, delivery, payment):
        options = {}

        delivery_description = 'Ridicare produse de la sediul ATEX Computer'
        if delivery:
            delivery_description = 'Livrare la adresa specificata'
        options['delivery_description'] = delivery_description

        payment_description = 'Plata '
        payment_cash_description = payment_description + ('ramburs' if delivery else 'numerar')
        if (payment == 'cash'):
            payment_description = payment_cash_description
        else:
            payment_description += 'prin transfer bancar/OP'
        options['payment_description'] = payment_description
        options['payment_cash_description'] = payment_cash_description

        return options
