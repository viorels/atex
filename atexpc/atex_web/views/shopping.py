from django.core.urlresolvers import reverse_lazy
from django.contrib.auth import authenticate, login
from django.views.generic.edit import FormView

from atexpc.atex_web.views.base import HybridGenericView
from atexpc.atex_web.models import DatabaseCart as Cart
from atexpc.atex_web.forms import user_form_factory

import logging
logger = logging.getLogger(__name__)


class CartBase(HybridGenericView):
    template_name = "cart.html"
    breadcrumbs = [{'name': "Cos cumparaturi"}]

    def get_json_context(self):
        return {'cart': self._get_cart_data()}

    def post(self, request, *args, **kwargs):
        method = request.POST.get('method')
        product_id = request.POST.get('product_id')
        if method == 'add':
            self._add_to_cart(product_id)
        return self.render_to_response(self.get_json_context())


class OrderBase(FormView, HybridGenericView):
    template_name = "order.html"
    breadcrumbs = CartBase.breadcrumbs + [{'name': "Date facturare"}]
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
                first_name=form.cleaned_data['firstname'],
                last_name=form.cleaned_data['surname'],
                password=form.cleaned_data['password1'],
                usertype=form.cleaned_data['usertype'])
            logger.info('Signup %s', result)
            user = authenticate(email=form.cleaned_data['email'],
                                password=form.cleaned_data['password1'])
            user.first_name = form.cleaned_data['firstname']
            user.last_name = form.cleaned_data['surname']
            user.save()
            user.userprofile.phone = form.cleaned_data['phone']
            user.userprofile.city = form.cleaned_data['city']
            user.userprofile.county = form.cleaned_data['county']
            user.userprofile.address = form.cleaned_data['address']
            user.userprofile.save()
        elif form.cleaned_data['logintype'] == 'old':
            user = authenticate(email=form.cleaned_data['user'],
                                password=form.cleaned_data['password'])
        if user is not None:    # user.is_active ?
            login(self.request, user)
            logger.info('Login %s', user.email)
        return super(OrderBase, self).form_valid(form)

    def form_invalid(self, form):
        logger.debug("OrderView.form_invalid" + str(form.errors))
        return super(OrderBase, self).form_valid(form)


class ConfirmBase(HybridGenericView):
    template_name = "confirm.html"
    breadcrumbs = OrderBase.breadcrumbs + [{'name': "Confirmare"}]


class ShoppingMixin(object):
    def get_context_data(self, **context):
        context.update({'cart': self._get_cart_data()})
        return super(ShoppingMixin, self).get_context_data(**context)

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
