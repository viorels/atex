from django.conf.urls import patterns, url
from django.conf.urls.static import static
from django.conf import settings
from django.shortcuts import render
from django.views.generic import RedirectView

from views import (HomeView, MySearchView, ProductsView, ProductView, BrandsView,
                   PromotionsView, GamingView, AppleView, BlackFridayView,
                   ContactView, ConditionsView, ServiceView, WarrantyServiceView,
                   CartView, OrderView, ConfirmView, LoginView,
                   RecoverPassword, RecoverPasswordDone, ResetPassword, ResetPasswordDone)
from views.products import SearchAutoComplete, DropboxWebHookView
from views.authentication import GetEmails
from views.shopping import GetCompanyInfo


urlpatterns = patterns('',
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^cauta/', MySearchView.as_view(), name='search'),
    url(r'^cauta_auto/', SearchAutoComplete.as_view()),
    url(r'^produse/(?P<category_id>\d+)-(?P<slug>.*)$',
        ProductsView.as_view(), name='category'),
    url(r'^produs/(?P<product_id>\d+)-(?P<slug>.*)$', ProductView.as_view(),
        name='product'),
    url(r'^dropbox-webhook/$', DropboxWebHookView.as_view()),
    url(r'^branduri/', BrandsView.as_view(), name='brands'),
    url(r'^cos/$', CartView.as_view(), name='cart'),
    url(r'^cos/comanda/', OrderView.as_view(), name='order'),
    url(r'^company_info/(?P<cif>\w+)$', GetCompanyInfo.as_view(), name='company_info'),
    url(r'^cos/confirma/', ConfirmView.as_view(), name='confirm'),
    url(r'^contact/', ContactView.as_view(), name='contact'),
    url(r'^conditii/', ConditionsView.as_view(), name='conditions'),
    url(r'^service/', ServiceView.as_view(), name='service'),
    url(r'^garantii-service-autorizat/', WarrantyServiceView.as_view(), name='warranty-service'),
    url(r'^promotii/', PromotionsView.as_view(), name='promotions'),
    url(r'^gaming/', GamingView.as_view(), name='gaming'),
    url(r'^apple/', AppleView.as_view(), name='apple'),
    # url(r'^Black-Friday/', BlackFridayView.as_view(), name='black-friday'),
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^login/emails/(?P<username>\w+)$', GetEmails.as_view()),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),

    url(r'^recover/(?P<signature>.+)/$', RecoverPasswordDone.as_view(),
        name='password_reset_sent'),
    url(r'^recover/$', RecoverPassword.as_view(), name='password_reset_recover'),
    url(r'^reset/done/$', ResetPasswordDone.as_view(), name='password_reset_done'),
    url(r'^reset/(?P<token>[\w:-]+)/$', ResetPassword.as_view(),
        name='password_reset_reset'),

    url(r'PIE\.htc$',
        lambda request: render(request, "PIE.htc", content_type="text/x-component")),
    # TODO: remove ledacy redirect sm.ashx to MEDIA_URL + SHOPMANIA_FEED_FILE
    url(r'^sm.ashx$', RedirectView.as_view(url='/media/shopmania.csv', permanent=True)),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
