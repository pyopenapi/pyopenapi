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


class HeaderConverterTestCase(unittest.TestCase):
    """ test case for header """

    def test_basic(self):
        header = app.s('p2').get.responses['200'].headers['X-TEST']

        obj = converters.to_header(header, '')
        self.assertEqual(obj['style'], 'simple')
        self.assertEqual(obj['schema']['type'], 'array')
        self.assertEqual(obj['schema']['items']['type'], 'string')


class ParameterConverterTestCase(unittest.TestCase):
    """ test case for parameter """

    def test_basic(self):
        p = app.s('p1').get.parameters[0]

        obj, pctx = converters.from_parameter(p, None, [], '')
        self.assertFalse(pctx.is_body)
        self.assertFalse(pctx.is_file)
        self.assertEqual(obj['style'], 'form')
        self.assertEqual(obj['explode'], True)
        self.assertEqual(obj['in'], 'query')
        self.assertEqual(obj['name'], 'status')

        _schema = obj['schema']
        self.assertEqual(_schema['default'], 'available')
        self.assertEqual(_schema['type'], 'array')

        _items = _schema['items']
        self.assertEqual(_items['type'], 'string')
        self.assertEqual(sorted(_items['enum']), sorted(['available', 'pending', 'sold']))

    def test_file_in_form(self):
        p = app.resolve('#/parameters/form_file')

        obj, pctx = converters.from_parameter(p, None, ['application/x-www-form-urlencoded'], '')
        self.assertTrue(pctx.is_body)
        self.assertTrue(pctx.is_file)

        _schema = obj['content']['application/x-www-form-urlencoded']['schema']['properties']['form_file']
        self.assertEqual(_schema['type'], 'string')
        self.assertEqual(_schema['format'], 'binary')

    def test_file_in_body(self):
        """ this is not a valid usage in 2.0, but someone suffer from that:
            https://github.com/OAI/OpenAPI-Specification/issues/1226
        """

        # normal body parameter with file type
        p = app.resolve('#/parameters/body_file')

        obj, pctx = converters.from_parameter(p, None, ['application/x-www-form-urlencoded'], '')
        self.assertTrue(pctx.is_body)
        self.assertTrue(pctx.is_file)
        _schema = obj['content']['application/x-www-form-urlencoded']['schema']['properties']['body_file']
        self.assertEqual(_schema['type'], 'string')
        self.assertEqual(_schema['format'], 'binary')

        # body parameter with $ref to schema with file type
        p = app.resolve('#/parameters/body_file_ref')

        obj, pctx = converters.from_parameter(p, None, ['application/x-www-form-urlencoded'], '')
        self.assertTrue(pctx.is_body)
        self.assertTrue(pctx.is_file)
        _schema = obj['content']['application/x-www-form-urlencoded']['schema']['properties']['body_file_ref']
        self.assertEqual(_schema['$ref'], '#/components/schemas/some_file')

class ResponseConverterTestCase(unittest.TestCase):
    """ test case for response """

    def test_basic(self):
        op = app.s('p1').get

        obj = converters.to_response(
            op.responses['200'],
            op.produces,
            ''
        )

        self.assertEqual(obj['description'], 'successful operation')
        self.assertTrue('content' in obj)
        _content = obj['content']
        self.assertTrue('application/json' in _content)
        self.assertTrue(_content['application/json']['schema']['items']['$ref'], '#/components/schemas/pet')
        self.assertTrue(_content['application/json']['schema']['type'], 'array')

    def test_with_header(self):
        op = app.s('p2').get

        obj = converters.to_response(
            op.responses['200'],
            [],
            ''
        )

        self.assertEqual(obj['description'], 'test for header')
        self.assertTrue('headers' in obj and 'X-TEST' in obj['headers'])
        _header = obj['headers']['X-TEST']
        self.assertEqual(_header['style'], 'simple')
        self.assertEqual(_header['schema']['items']['type'], 'string')
        self.assertEqual(_header['schema']['type'], 'array')


class OperationConverterTestCase(unittest.TestCase):
    """ test case for operation """

    def test_basic(self):
        op = app.s('p1').get

        obj = converters.to_operation(op, 'test_root', '')
        self.assertTrue('responses' in obj and '200' in obj['responses'])
        _response = obj['responses']['200']
        self.assertEqual(_response['description'], 'successful operation')
        self.assertTrue(
            'content' in _response and
            'application/json' in _response['content'] and
            'schema' in _response['content']['application/json']
        )
        _schema = _response['content']['application/json']['schema']
        self.assertEqual(_schema['items']['$ref'], '#/components/schemas/pet')
        self.assertEqual(_schema['type'], 'array')
        self.assertTrue('parameters' in obj and len(obj['parameters']) > 0)
        _parameter = obj['parameters'][0]
        self.assertEqual(_parameter['style'], 'form')
        self.assertEqual(_parameter['explode'], True)
        self.assertEqual(_parameter['in'], 'query')
        self.assertEqual(_parameter['name'], 'status')
        _schema = _parameter['schema']
        self.assertEqual(_schema['default'], 'available')
        self.assertEqual(_schema['type'], 'array')
        self.assertEqual(sorted(_schema['items']['enum']), sorted(['available', 'pending', 'sold']))
        self.assertEqual(_schema['items']['type'], 'string')

    def test_multiple_file_with_other_type(self):
        op = app.s('p1').post

        obj = converters.to_operation(op, 'test_root', '')

        # requestBody
        self.assertEqual(obj['requestBody']['required'], True)
        _media_type = obj['requestBody']['content']['multipart/form-data']
        _encoding = _media_type['encoding']
        self.assertEqual(_encoding['picture'], {'contentType':'application/octet-stream'})
        self.assertEqual(_encoding['description'], {'contentType':'text/plain'})
        self.assertEqual(_encoding['thumbnail'], {'contentType':'application/octet-stream'})
        _properties = _media_type['schema']['properties']
        self.assertEqual(_properties['picture'], {'type': 'string', 'format': 'binary'})
        self.assertEqual(_properties['description'], {'type': 'string'})
        self.assertEqual(_properties['thumbnail'], {'type': 'string', 'format': 'binary'})

        # response
        self.assertEqual(obj['responses']['200']['description'], 'successful operation')

    def test_parameter_ref(self):
        """ test parameters declared with '$ref'
        """
        op = app.s('p2').post

        obj = converters.to_operation(op, 'test_root', '')

        _content = obj['requestBody']['content']
        self.assertTrue('application/x-www-form-urlencoded' in _content)
        _properties = _content['application/x-www-form-urlencoded']['schema']['properties']
        self.assertTrue('form_file' in _properties)
        self.assertEqual(_properties['form_file']['$ref'], '#/components/requestBodies/form_file/content/multipart~1form-data/schema/properties/form_file')
        self.assertTrue('description' in _properties)
        self.assertEqual(_properties['description']['$ref'], '#/components/requestBodies/form_string/content/application~1x-www-form-urlencoded/schema/properties/description')
        _encoding = _content['application/x-www-form-urlencoded']['encoding']
        self.assertTrue('form_file' in _encoding)
        self.assertEqual(_encoding['form_file']['contentType'], 'application/octet-stream')
        self.assertTrue('description' in _encoding)
        self.assertEqual(_encoding['description']['contentType'], 'text/plain')

        _parameter = obj['parameters'][0]
        self.assertEqual(_parameter['$ref'], '#/components/parameters/query_string')

