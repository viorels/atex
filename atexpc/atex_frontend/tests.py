"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.utils import override_settings

import views

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

# TODO: disable cache
@override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3'}})
class ViewTest(TestCase): 
    def test_menu_categories_in(self):
        print getattr(views._get_menu, 'categories_in')() 
        self.assertTrue(True)

