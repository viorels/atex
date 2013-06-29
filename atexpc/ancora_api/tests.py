"""
run "manage.py test --settings=atexpc.config.test ancora_api"
"""

from django.test import TestCase
from api import Ancora, MockAdapter, AncoraAdapter

class CategoryTest(TestCase):
    def test_categories(self):
        """
        Tests that categories.xml file is read correctly
        """
        ancora = Ancora(adapter=MockAdapter(cache=None))
        categories = ancora.categories()
        self.assertEqual(categories[0]["name"], "Laptop & Desktop & Servere")

    def test_uri_with_args(self):
        """
        Tests that uri_with_args builds a correct url
        """
        base_uri = 'http://server.com/path/method?some=arg'
        adapter = AncoraAdapter(base_uri=base_uri)
        new_uri = adapter.uri_with_args(base_uri, method='new_method', args={'new': 'args'})
        self.assertEqual(new_uri, 'http://server.com/path/new_method?new=args&some=arg')