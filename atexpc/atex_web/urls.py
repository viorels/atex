from django.conf.urls import patterns, url
from django.conf.urls.static import static
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import RedirectView
from views import (HomeView, SearchView, ProductView, BrandsView,
                   ContactView, ConditionsView, ServiceView, ContestView,
                   BlackFriday, BlackFridaySoon,
                   CartView, OrderView, ConfirmView, LoginView,
                   RecoverPassword, RecoverPasswordDone, ResetPassword, ResetPasswordDone)
from views.authentication import GetEmails
from views.shopping import GetCompanyInfo


urlpatterns = patterns('',
#    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^$', BlackFridaySoon.as_view(), name='home'),
#    url(r'^$', RedirectView.as_view(url='/blackfriday', permanent=False), name='home'),
    url(r'^cauta/', SearchView.as_view(), name='search'),
    url(r'^produse/(?P<category_id>\d+)-(?P<slug>.*)$',
        SearchView.as_view(), name='category'),
    url(r'^produs/(?P<product_id>\d+)-(?P<slug>.*)$', ProductView.as_view(),
        name='product'),
    url(r'^branduri/', BrandsView.as_view(), name='brands'),
    url(r'^cos/$', CartView.as_view(), name='cart'),
    url(r'^cos/comanda/', OrderView.as_view(), name='order'),
    url(r'^company_info/(?P<cif>\w+)$', GetCompanyInfo.as_view(), name='company_info'),
    url(r'^cos/confirma/', ConfirmView.as_view(), name='confirm'),
    url(r'^contact/', ContactView.as_view(), name='contact'),
    url(r'^conditii/', ConditionsView.as_view(), name='conditions'),
    url(r'^service/', ServiceView.as_view(), name='service'),
    url(r'^concurs/', ContestView.as_view(), name='contest'),
    url(r'^blackfriday/', BlackFriday.as_view()),
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
    url(r'^sm.ashx$', RedirectView.as_view(url='/media/shopmania.csv')),
    url(r'^mu-57ecd7e2-71e9ba0b-ed0167ef-eabce26a$', lambda r: HttpResponse("42")), # blitz.io
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
