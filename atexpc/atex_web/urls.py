from django.conf.urls import patterns, url
from django.conf.urls.static import static
from django.conf import settings
from django.shortcuts import render
from django.views.generic import RedirectView
from views import (GenericView, HomeView, SearchView, ProductView, BrandsView, ContactView, ConditionsView,
                   CartView, OrderView, ConfirmView)


urlpatterns = patterns('',
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^cauta/', SearchView.as_view(), name='search'),
    url(r'^produse/(?P<category_id>\d+)-(?P<slug>.*)$',
        SearchView.as_view(), name='category'),
    url(r'^produs/(?P<product_id>\d+)-(?P<slug>.*)$', ProductView.as_view(),
        name='product'),
    url(r'^branduri/', BrandsView.as_view(), name='brands'),
    url(r'^cos/$', CartView.as_view(), name='cart'),
    url(r'^cos/comanda/', OrderView.as_view(), name='order'),
    url(r'^cos/confirma/', ConfirmView.as_view(), name='confirm'),
    url(r'^contact/', ContactView.as_view(), name='contact'),
    url(r'^conditii/', ConditionsView.as_view(), name='conditions'),
    url(r'^service/', GenericView.as_view(template_name='service.html'), name='service'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'PIE\.htc$',
        lambda request: render(request, "PIE.htc", content_type="text/x-component")),
    # TODO: remove ledacy redirect sm.ashx to MEDIA_URL + SHOPMANIA_FEED_FILE
    url(r'^sm.ashx$', RedirectView.as_view(url='/media/shopmania.csv')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
