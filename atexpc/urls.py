from django.conf.urls import patterns, include, url
from django.conf import settings
from django.http import HttpResponse

from .atex_web.views import ErrorView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^', include('atexpc.atex_web.urls')),
    url(r'^', include('social.apps.django_app.urls', namespace='social')),
    url(r'^admin/', include(admin.site.urls)),
)

handler404 = ErrorView.as_view(error_code=404)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^404/$', handler404),
        (r'^500/$', ErrorView.as_view(error_code=500)),
        (r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /",
                                                 content_type="text/plain")),
    )
