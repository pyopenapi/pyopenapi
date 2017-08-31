from ..utils import get_test_data_folder
from ...core import App
from ...scanner.v2_0.upgrade import converters
import unittest
import os
import six


app = App.load(get_test_data_folder(
    version='2.0',
    which='upgrade'
))
app.prepare(strict=False)

class ExternalDocConverterTestCase(unittest.TestCase):
    """ test case for externalDoc converter """

    def test_external_doc(self):
        ex_doc = app.resolve('#/externalDocs')

        obj = converters.to_external_docs(ex_doc, '')
        self.assertTrue('url' in obj)
        self.assertEqual(obj['url'], ex_doc.url)
        self.assertTrue('description' in obj)
        self.assertEqual(obj['description'], ex_doc.description)


class ItemsConverterTestCase(unittest.TestCase):
    """ test case for items converter """

    def test_with_type(self):
        items = app.s('p1').get.parameters[0].items

        obj = converters.from_items(items, '')
        self.assertEqual(obj['type'], getattr(items, 'type'))

    def test_with_ref(self):
        items = app.s('p1').get.responses['200'].schema.items

        obj = converters.from_items(items, '')
        self.assertEqual(obj['$ref'], '#/components/schemas/pet')


class TagConverterTestCase(unittest.TestCase):
    """ test case for tag converter """

    def test_basic(self):
        tags = app.resolve('#/tags')

        obj = converters.to_tag(tags[0], '')
        self.assertEqual(obj['name'], tags[0].name)
        self.assertEqual(obj['description'], tags[0].description)
        self.assertTrue('externalDocs' in obj)
        self.assertEqual(obj['externalDocs']['url'], tags[0].externalDocs.url)


class XMLConverterTestCase(unittest.TestCase):
    """ test case for XML converter """

    def test_basic(self):
        pet = app.resolve('#/definitions/pet')

        x = pet.properties['photoUrls'].xml
        obj = converters.to_xml(x, '')
        self.assertEqual(obj['name'], x.name)
        self.assertEqual(obj['wrapped'], x.wrapped)


class SchemaConverterTestCase(unittest.TestCase):
    """ test case for schema converter """

    def test_basic(self):
        pet = app.resolve('#/definitions/pet')

        obj = converters.to_schema(pet, '')
        self.assertEqual(obj['required'], pet.required)
        _id = obj['properties']['id']
        self.assertEqual(_id['type'], 'integer')
        self.assertEqual(_id['format'], 'int64')
        _category = obj['properties']['category']
        self.assertEqual(_category['$ref'], '#/components/schemas/category')
        _photo_urls = obj['properties']['photoUrls']
        self.assertEqual(_photo_urls['type'], 'array')
        self.assertEqual(_photo_urls['items']['type'], 'string')
        _status = obj['properties']['status']
        self.assertEqual(sorted(_status['enum']), sorted(['available', 'pending', 'sold']))


class SecuritySchemeConverterTestCase(unittest.TestCase):
    """ test case for security scheme """

    def test_basic(self):
        auth = app.resolve('#/securityDefinitions/petstore_auth')

        obj = converters.to_security_scheme(auth, '')
        self.assertEqual(obj['type'], 'oauth2')
        flows = obj['flows']['implicit']
        self.assertEqual(flows['authorizationUrl'], 'http://petstore.swagger.io/api/oauth/dialog')
        self.assertTrue('write:pets' in flows['scopes'])
        self.assertTrue('read:pets' in flows['scopes'])

