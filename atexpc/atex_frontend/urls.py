from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^products/', views.products, name='products'),
)
