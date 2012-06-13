from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
    url(r'^produse/', views.products, name='products'),
)
