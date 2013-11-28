from authentication import (LoginBase, RecoverPasswordView, RecoverPasswordDoneView,
                            ResetPasswordView, ResetPasswordDoneView)
from products import (HomeBase, SearchBase, ProductBase, BrandsBase,
                      SearchMixin)
from shopping import CartBase, OrderBase, ConfirmBase, ShoppingMixin
from base import BaseView, BreadcrumbsMixin, ErrorBase

from django.shortcuts import redirect
from pytz import timezone

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

class ContestView(CommonMixins, BaseView):
    template_name = "contest.html"
    breadcrumbs = [{'name': "Concurs"}]

class BlackFridaySoon(CommonMixins, BaseView):
    template_name = "blackfriday-soon.html"

class BlackFriday(CommonMixins, BaseView):
    template_name = "blackfriday.html"
    blackfriday = datetime(2013, 11, 29, 10, 0, 0)

    def is_black_friday(self):
        cluj = timezone('Europe/Bucharest')
        black_friday_cluj = cluj.localize(self.blackfriday)
        now_cluj = cluj.normalize(datetime.now(tz=pytz.utc).astimezone(cluj))
        return now_cluj > black_friday_cluj

    def dispatch(self, request, *args, **kwargs):
        if not is_black_friday():
            return redirect('/')
        else:
            return super(BlackFriday, self).dispatch(request, *args, **kwargs)
