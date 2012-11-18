"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from api import Ancora, MockAdapter

class CategoryTest(TestCase):
    def test_categories(self):
        """
        Tests that categories.xml file is read correctly
        """
        ancora = Ancora(adapter=MockAdapter(cache=None))
        categories = ancora.categories()
        self.assertEqual(categories[0]["name"], "Laptop & Desktop & Servere")
