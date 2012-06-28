from django.conf.urls import patterns, url
from django.views.generic.simple import direct_to_template
import views

urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
    url(r'^cauta/', views.search, name='search'),
    url(r'^produse/(?P<category_id>[0-9.]+)-(?P<slug>.*)$', views.search, name='category'),
    url(r'^produs/', views.product, name='product'),
    url(r'^cos/$', views.cart, name='cart'),
    url(r'^cos/comanda/', views.order, name='order'),
    url(r'^cos/confirma/', views.confirm, name='confirm'),
    url(r'PIE\.htc$', views.pie),
)
