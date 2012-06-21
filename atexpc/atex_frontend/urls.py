from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
    url(r'^cauta/', views.search, name='search'),
    url(r'^produs/', views.product, name='product'),
    url(r'^cos/', views.cart, name='cart'),
)
