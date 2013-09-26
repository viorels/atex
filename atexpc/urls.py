from django.conf.urls import patterns, include, url
from django.conf import settings

from atex_web.views import ErrorView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^', include('atexpc.atex_web.urls')),
    url(r'', include('social_auth.urls')),
    url(r'', include('password_reset.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

handler404 = ErrorView.as_view(error_code=404)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^404/$', handler404),
        (r'^500/$', ErrorView.as_view(error_code=500)),
    )
