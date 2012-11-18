"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

import views


class ClientTest(TestCase):
    def test_home(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template[0].name, 'home.html')
        self.assertEqual(len(response.context['recommended']), 5)
        self.assertContains(response, "Bun venit")


class ViewsTest(TestCase): 
    def test_menu_categories_in(self):
        #print getattr(views._get_menu, 'categories_in')() 
        self.assertTrue(True)

    def test_uri_with_args_no_change(self):
    	any_uri = 'http://any.com/uri?with=args&something=else'
    	result = views._uri_with_args(any_uri)
    	self.assertEqual(any_uri, result)

    def test_uri_with_args_add_something(self):
    	any_uri = 'http://any.com/uri?with=args'
    	result = views._uri_with_args(any_uri, something='new')
    	expected_result = any_uri + '&something=new'
    	self.assertEqual(expected_result, result)

    def test_uri_with_args_preserve_multiple_values(self):
    	uri_with_multiple_values = 'http://uri.com/?f=1&f=2'
    	result = views._uri_with_args(uri_with_multiple_values)
    	self.assertEqual(uri_with_multiple_values, result)

    def test_uri_with_args_overwrite_multiple_values(self):
    	uri_with_multiple_values = 'http://uri.com/?f=1&f=2'
    	result = views._uri_with_args(uri_with_multiple_values, f=3)
    	expected = 'http://uri.com/?f=3'
    	self.assertEqual(result, expected)

