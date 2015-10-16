from authentication import (LoginBase, RecoverPasswordView, RecoverPasswordDoneView,
                            ResetPasswordView, ResetPasswordDoneView)
from products import (HomeBase, SearchBase, ProductBase, BrandsBase,
                      SearchMixin)
from shopping import CartBase, OrderBase, ConfirmBase, ShoppingMixin
from base import BaseView, BreadcrumbsMixin, ErrorBase

# *Base classes (e.g. HomeView must be last on inheritance list as
# TemplateView.get_context_data breaks the cooperative multiple inheritance chain

class CommonMixins(SearchMixin, BreadcrumbsMixin, ShoppingMixin):
    pass

class HomeView(CommonMixins, HomeBase):
    pass

class ProductView(CommonMixins, ProductBase):
    pass

class SearchView(ShoppingMixin, BreadcrumbsMixin, SearchBase):
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

class PromotionsView(CommonMixins, BaseView):
    template_name = "promotions.html"
    breadcrumbs = [{'name': "Promotii"}]

class GamingView(CommonMixins, BaseView):
    template_name = "gaming.html"
    breadcrumbs = [{'name': "Gaming"}]

class AppleView(CommonMixins, BaseView):
    template_name = "apple.html"
    breadcrumbs = [{'name': "Apple"}]

class BlackFridayView(CommonMixins, BaseView):
    template_name = "black_friday.html"
    breadcrumbs = [{'name': "Black Friday"}]

