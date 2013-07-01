"""
run "manage.py test --settings=atexpc.config.test ancora_api"
"""

from django.test import TestCase
from mock import Mock
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

    def test_create_user(self):
        """
        Tests that create_user posts to the correct url
        """
        base_uri = 'http://server.com/path/method?some=arg'
        expected_uri = 'http://server.com/path/saveForm.do?iduser=47&cod_formular=1312&actiune=SAVE_TAB&some=arg&pid=0'
        expected_args = {'denumire': 'John Doe', 'email': 'john@doe.com', 'parola': None}

        adapter = AncoraAdapter(base_uri=base_uri)
        adapter.write = Mock()
        ancora = Ancora(adapter=adapter) 
        ancora.create_user(email='john@doe.com', fname='John', lname='Doe', password='pass')

        called_with = adapter.write.call_args[0]
        expected_args['parola'] = called_with[1]['parola']
        self.assertEqual((expected_uri, expected_args), called_with)

    def test_get_user(self):
        base_uri = 'http://server.com/path/jis.serv?database=atex'
        email = 'user@email.com'
        password = 'pass'
        expected_uri = ('http://server.com/path/jis.serv?'
                        'fparola=hashed_pass&cod_formular=1023&femail=user%40email.com&database=atex')

        adapter = AncoraAdapter(base_uri=base_uri)
        adapter.read = Mock()
        ancora = Ancora(adapter=adapter)
        ancora._password_hash = Mock()
        ancora._password_hash.return_value = 'hashed_pass'
        user = ancora.get_user(email=email, password=password)
        called_with = adapter.read.call_args[0]
        self.assertEqual(expected_uri, called_with[0])

