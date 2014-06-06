"""
run "./manage.py test --settings=atexpc.config.test atexpc.atex_web".
"""

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.contrib.sessions.backends.db import SessionStore
from mock import patch

from models import Product, ProductManager, DatabaseCart
from ancora_api import AncoraAPI
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


class ModelsTest(TestCase):
    def test_add_existing_model_with_new_id(self):
        product = {'id': 22910, 'model': 'DIR-615', 'name': 'test product'}
        new_product = product.copy()
        new_product.update(id=1)

        with patch.object(ProductManager, 'get_product') as mock_get_product:
            mock_get_product.return_value = product
            Product.objects.get_and_save(product['id'])
            mock_get_product.assert_called_with(product['id'])
            self.assertEqual(Product.objects.get(id=product['id']).model, product['model'])

            mock_get_product.return_value = new_product
            try:
                Product.objects.get_and_save(new_product['id'])
            except IntegrityError as e:
                self.fail("get_and_save raised %s: %s" % (type(e).__name__, e))


class AncoraTest(TestCase):
    def test_categories(self):
        ancora = AncoraAPI()
        self.assertTrue(len(ancora.categories.get_all()) > 0)


class DatabaseCartTest(TestCase):
    def setUp(self):
        session = SessionStore()
        session.save()
        self.cart = DatabaseCart.create(session_id=session.session_key)

    def _create_product(self, name):
        product = Product.objects.create(name=name, model=name[-10:])
        product.save()
        return product

    def test_add_product_increases_count(self):
        p = self._create_product("Test product 1")
        self.cart.add_item(p.id)
        self.assertEqual(self.cart.count(), 1)

    def test_add_delete_product_keeps_count_0(self):
        p = self._create_product("Test product 1")
        self.cart.add_item(p.id)
        self.cart.remove_item(p.id)
        self.assertEqual(self.cart.count(), 0)

    def test_add_2_delete_1_results_count_1(self):
        p1 = self._create_product("Test product 1")
        self.cart.add_item(p1.id)
        p2 = self._create_product("Test product 2")
        self.cart.add_item(p2.id)
        self.cart.remove_item(p1.id)
        self.assertEqual(self.cart.count(), 1)

    def test_add_product_twice_results_count_2_and_total_count_1(self):
        p = self._create_product("Test product 1")
        self.cart.add_item(p.id)
        self.cart.add_item(p.id)
        self.assertEqual(self.cart.count(), 1)
        self.assertEqual(self.cart.items()[0]['count'], 2)

    def test_add_product_update_count(self):
        p = self._create_product("Test product 1")
        self.cart.add_item(p.id)
        self.cart.update_item(p.id, 3)
        self.assertEqual(self.cart.count(), 1)
        self.assertEqual(self.cart.items()[0]['count'], 3)

    def test_add_product_returns_product(self):
        p = self._create_product("Test product 1")
        added = self.cart.add_item(p.id)
        self.assertTrue(added is not None and added.id == p.id)

    def test_remove_product_returns_product(self):
        p = self._create_product("Test product 1")
        self.cart.add_item(p.id)
        removed = self.cart.remove_item(p.id)
        self.assertTrue(removed is not None and removed.id == p.id)

    def test_remove_product_not_in_cart_returns_none(self):
        p = self._create_product("Test product 1")
        removed = self.cart.remove_item(p.id)
        self.assertTrue(removed is None) 

    inexistent_id = 100

    def test_add_inexistent_product_returns_none(self):
        added = self.cart.add_item(self.inexistent_id)
        self.assertTrue(added is None)

    def test_remove_inexistent_product_returns_none(self):
        removed = self.cart.remove_item(self.inexistent_id)
        self.assertTrue(removed is None)
