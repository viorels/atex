from authentication import (LoginBase, RecoverPasswordView, RecoverPasswordDoneView,
                            ResetPasswordView, ResetPasswordDoneView)
from products import (HomeView, SearchBase, ProductsBase, ProductBase, BrandsBase,
                      SearchMixin)
from shopping import CartBase, OrderBase, ConfirmBase, ShoppingMixin
from base import BaseView, AncoraMixin, BreadcrumbsMixin, ErrorBase

# *Base classes (e.g. HomeView must be last on inheritance list as
# TemplateView.get_context_data breaks the cooperative multiple inheritance chain

class CommonMixins(SearchMixin, BreadcrumbsMixin, ShoppingMixin, AncoraMixin):
    pass

class HomeView(CommonMixins, HomeView):
    pass

class ProductView(CommonMixins, ProductBase):
    pass

class ProductsView(ShoppingMixin, BreadcrumbsMixin, AncoraMixin, ProductsBase):
    pass

class SearchView(ShoppingMixin, BreadcrumbsMixin, AncoraMixin, SearchBase):
    pass

class BrandsView(CommonMixins, BrandsBase):
    pass

class CartView(CommonMixins, CartBase):
    pass

class OrderView(CommonMixins, OrderBase):
    pass

class ConfirmView(CommonMixins, ConfirmBase):
    pass

class LoginView(CommonMixins, LoginBase): pass

class RecoverPassword(CommonMixins, RecoverPasswordView): pass
class RecoverPasswordDone(CommonMixins, RecoverPasswordDoneView): pass
class ResetPassword(CommonMixins, ResetPasswordView): pass
class ResetPasswordDone(CommonMixins, ResetPasswordDoneView): pass

class ErrorView(BreadcrumbsMixin, SearchMixin, ErrorBase):
    pass

class ContactView(CommonMixins, BaseView):
    breadcrumbs = [{'name': "Contact"}]

    def get_template_names(self):
        return "contact-%s.html" % self._get_base_domain()

class ConditionsView(CommonMixins, BaseView):
    template_name = "conditions.html"
    breadcrumbs = [{'name': "Conditii Vanzare"}]

class ServiceView(CommonMixins, BaseView):
    template_name = "service.html"
    breadcrumbs = [{'name': "Servicii"}]

class ContestView(CommonMixins, BaseView):
    template_name = "contest.html"
    breadcrumbs = [{'name': "Concurs"}]

