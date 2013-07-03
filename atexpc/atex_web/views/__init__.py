from products import (HomeBase, SearchBase, ProductBase, BrandsBase,
                      ContactBase, ConditionsBase,
                      SearchMixin, BreadcrumbsMixin)
from products import CartBase, OrderBase, ConfirmBase, ShoppingMixin
from products import BaseView, ErrorBase

# *Base classes (e.g. HomeView must be last on inheritance list as
# TemplateView.get_context_data breaks the cooperative multiple inheritance chain

class HomeView(ShoppingMixin, SearchMixin, HomeBase):
    pass

class ProductView(ShoppingMixin, SearchMixin, BreadcrumbsMixin, ProductBase):
    pass

class SearchView(ShoppingMixin, BreadcrumbsMixin, SearchBase):
    pass

class BrandsView(ShoppingMixin, SearchMixin, BreadcrumbsMixin, BrandsBase):
    pass

class CartView(ShoppingMixin, SearchMixin, CartBase):
    pass

class OrderView(ShoppingMixin, SearchMixin, OrderBase):
    pass

class ConfirmView(ShoppingMixin, SearchMixin, ConfirmBase):
    pass

class ContactView(ShoppingMixin, BreadcrumbsMixin, SearchMixin, ContactBase):
    pass

class ConditionsView(BreadcrumbsMixin, SearchMixin, ConditionsBase):
    pass

class GenericView(BaseView):
    pass

class ErrorView(BreadcrumbsMixin, SearchMixin, ErrorBase):
    pass
