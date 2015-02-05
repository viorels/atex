from django.contrib.sites.models import get_current_site
from django.views.generic.base import TemplateView

from base import BreadcrumbsMixin, ErrorBase
from authentication import (LoginBase, RecoverPasswordView, RecoverPasswordDoneView,
                            ResetPasswordView, ResetPasswordDoneView)
from products import (HomeView, SearchView, ProductsView, ProductView, BrandsBase,
                      SearchMixin)
from shopping import CartBase, OrderBase, ConfirmBase, ShoppingMixin


# *Base classes (e.g. HomeView must be last on inheritance list as
# TemplateView.get_context_data breaks the cooperative multiple inheritance chain

# class HomeView(BreadcrumbsMixin, HomeView):
#     pass

# class ProductView(BreadcrumbsMixin, ProductBase):
#     pass

# class ProductsView(BreadcrumbsMixin, ProductsBase):
#     pass

# class SearchView(BreadcrumbsMixin, SearchBase):
#     pass

class BrandsView(BreadcrumbsMixin, BrandsBase):
    pass

class CartView(BreadcrumbsMixin, CartBase):
    pass

class OrderView(BreadcrumbsMixin, OrderBase):
    pass

class ConfirmView(BreadcrumbsMixin, ConfirmBase):
    pass

class LoginView(BreadcrumbsMixin, LoginBase): pass

class RecoverPassword(BreadcrumbsMixin, RecoverPasswordView): pass
class RecoverPasswordDone(BreadcrumbsMixin, RecoverPasswordDoneView): pass
class ResetPassword(BreadcrumbsMixin, ResetPasswordView): pass
class ResetPasswordDone(BreadcrumbsMixin, ResetPasswordDoneView): pass

class ErrorView(BreadcrumbsMixin, ErrorBase):
    pass

class ContactView(BreadcrumbsMixin, TemplateView):
    breadcrumbs = [{'name': "Contact"}]

    def get_template_names(self):
        return "contact-%s.html" % _get_base_domain(self.request)

class ConditionsView(BreadcrumbsMixin, TemplateView):
    template_name = "conditions.html"
    breadcrumbs = [{'name': "Conditii Vanzare"}]

class ServiceView(BreadcrumbsMixin, TemplateView):
    template_name = "service.html"
    breadcrumbs = [{'name': "Servicii"}]

class ContestView(BreadcrumbsMixin, TemplateView):
    template_name = "contest.html"
    breadcrumbs = [{'name': "Concurs"}]

# TODO: import from middleware
def _get_base_domain(request):
    """Get the last 2 segments of the domain name"""
    domain = get_current_site(request).domain
    return '.'.join(domain.split('.')[-2:])
