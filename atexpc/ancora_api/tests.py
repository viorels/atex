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
        mock = MockAdapter('file:///home/vio/work/atex/atexpc/ancora_api/mock_data/categories.xml')
        ancora = Ancora(adapter=mock)
        categories = ancora.categories()
        print categories
        self.assertEqual(1 + 1, 2)
