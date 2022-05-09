from django.conf import settings
from django.conf.urls import include, url
from django.http import HttpResponse

from .atex_web.views import ErrorView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^', include('atexpc.atex_web.urls')),
    url(r'^', include('social_django.urls', namespace='social')),
    url(r'^admin/', admin.site.urls),
]

handler404 = ErrorView.as_view(error_code=404)

if settings.DEBUG:
    urlpatterns += [
        url(r'^404/$', handler404),
        url(r'^500/$', ErrorView.as_view(error_code=500)),
        url(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /",
                                                    content_type="text/plain")),
    ]
