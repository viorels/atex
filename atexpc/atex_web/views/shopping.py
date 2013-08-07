from django.core.urlresolvers import reverse_lazy
from django.contrib.auth import authenticate, login
from django.views.generic.edit import FormView

from atexpc.atex_web.views.base import HybridGenericView
from atexpc.atex_web.models import CartFactory
from atexpc.atex_web.forms import user_form_factory
from atexpc.atex_web.utils import FrozenDict
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
        return self.render_to_response(self.get_json_context())


class LoginBase(FormView, HybridGenericView):
    template_name = "login.html"
    breadcrumbs = CartBase.breadcrumbs + [FrozenDict(name="Login/Signup",
                                                     url=reverse_lazy('login'))]
    success_url = reverse_lazy('home')

    def get_form_class(self):
        logintype = self.request.POST.get('logintype', None)
        return user_form_factory(logintype)

    def form_valid(self, form):
        login(self.request, form.get_user())
        logger.info('Login %s', self.request.user.email)
        return super(LoginBase, self).form_valid(form)


class OrderBase(LoginBase):
    template_name = "order.html"
    breadcrumbs = CartBase.breadcrumbs + [FrozenDict(name="Date facturare",
                                                     url=reverse_lazy('order'))]
    success_url = reverse_lazy('confirm')


class ConfirmBase(HybridGenericView):
    template_name = "confirm.html"
    breadcrumbs = OrderBase.breadcrumbs + [FrozenDict(name="Confirmare",
                                                      url=reverse_lazy('confirm'))]


class ShoppingMixin(object):
    def get_context_data(self, **context):
        context.update({'cart': self._get_cart_data()})
        return super(ShoppingMixin, self).get_context_data(**context)

    def _get_cart(self):
        cart_id = self.request.session.get('cart_id')
        cart = CartFactory(api=self.api).get(cart_id) if cart_id else None
        return cart

    def _create_cart(self):
        # TODO: are cookies enabled ?
        guest_id = 0
        ancora_user_id = self.request.user.ancora_id or guest_id
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
