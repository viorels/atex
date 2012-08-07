from django.conf.urls import patterns, url
from django.conf.urls.static import static
from django.conf import settings
import views

urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
    url(r'^cauta/', views.search, name='search'),
    url(r'^produse/(?P<category_id>\d+)-(?P<slug>.*)$', views.search, name='category'),
    url(r'^produs/', views.product, name='product'),
    url(r'^cos/$', views.cart, name='cart'),
    url(r'^cos/comanda/', views.order, name='order'),
    url(r'^cos/confirma/', views.confirm, name='confirm'),
    url(r'PIE\.htc$', views.pie),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
