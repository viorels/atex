from django.conf import settings
from django.core.cache import cache
from django.contrib.sites.models import Site

# https://bitbucket.org/wkornewald/djangotoolbox/src/535feb981c50/djangotoolbox/sites/dynamicsite.py

_default_site_id = getattr(settings, 'SITE_ID', None)

class DynamicSiteIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    """Sets settings.SITE_ID based on request's domain"""
    def __call__(self, request):
        # Ignore port if it's 80 or 443
        if ':' in request.get_host():
            domain, port = request.get_host().split(':')
            if int(port) not in (80, 443):
                domain = request.get_host()
        else:
            domain = request.get_host().split(':')[0]

        # Domains are case insensitive
        domain = domain.lower()

        # We cache the SITE_ID
        cache_key = 'Site:domain:%s' % domain
        site = cache.get(cache_key)
        if site:
            SITE_ID.value = site
        else:
            try:
                site = Site.objects.get(domain=domain)
            except Site.DoesNotExist:
                site = None

            if not site:
                # Fall back to with/without 'www.'
                if domain.startswith('www.'):
                    fallback_domain = domain[4:]
                else:
                    fallback_domain = 'www.' + domain

                try:
                    site = Site.objects.get(domain=fallback_domain)
                except Site.DoesNotExist:
                    site = None

            # Add site if it doesn't exist
            if not site and getattr(settings, 'CREATE_SITES_AUTOMATICALLY',
                                    True):
                site = Site(domain=domain, name=domain)
                site.save()

            # Set SITE_ID for this thread/request
            if site:
                SITE_ID.value = site.pk
            else:
                SITE_ID.value = _default_site_id

            cache.set(cache_key, SITE_ID.value, 5*60)

        response = self.get_response(request)
        return response

def make_tls_property(default=None):
    """Creates a class-wide instance property with a thread-specific value."""
    class TLSProperty:
        def __init__(self):
            from threading import local
            self.local = local()

        def __get__(self, instance, cls):
            if not instance:
                return self
            return self.value

        def __set__(self, instance, value):
            self.value = value

        def _get_value(self):
            return getattr(self.local, 'value', default)
        def _set_value(self, value):
            self.local.value = value
        value = property(_get_value, _set_value)

    return TLSProperty()

SITE_ID = settings.__class__.SITE_ID = make_tls_property()
