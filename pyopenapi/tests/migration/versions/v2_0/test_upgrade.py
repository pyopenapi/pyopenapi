import unittest

from pyopenapi.migration.versions.v2_0.scanner.upgrade import converters
from ....utils import get_test_data_folder, SampleApp

_APP = SampleApp.create(
    get_test_data_folder(version='2.0', which='upgrade'), to_spec_version='2.0')


class ExternalDocConverterTestCase(unittest.TestCase):
    """ test case for externalDoc converter """

    def test_external_doc(self):
        ex_doc, _ = _APP.resolve_obj('#/externalDocs', from_spec_version='2.0')

        obj = converters.to_external_docs(ex_doc, '')
        self.assertTrue('url' in obj)
        self.assertEqual(obj['url'], ex_doc.url)
        self.assertTrue('description' in obj)
        self.assertEqual(obj['description'], ex_doc.description)


class ItemsConverterTestCase(unittest.TestCase):
    """ test case for items converter """

    def test_with_type(self):
        items, _ = _APP.resolve_obj(
            '#/paths/~1p1/get/parameters/0/items', from_spec_version='2.0')

        obj = converters.from_items(items, '')
        self.assertEqual(obj['type'], getattr(items, 'type'))

    def test_with_ref(self):
        items, _ = _APP.resolve_obj(
            '#/paths/~1p1/get/responses/200/schema/items',
            from_spec_version='2.0')

        obj = converters.from_items(items, '')
        self.assertEqual(obj['$ref'], '#/definitions/pet')


class TagConverterTestCase(unittest.TestCase):
    """ test case for tag converter """

    def test_basic(self):
        tags, _ = _APP.resolve_obj('#/tags', from_spec_version='2.0')

        obj = converters.to_tag(tags[0], '')
        self.assertEqual(obj['name'], tags[0].name)
        self.assertEqual(obj['description'], tags[0].description)
        self.assertTrue('externalDocs' in obj)
        self.assertEqual(obj['externalDocs']['url'], tags[0].externalDocs.url)


class XMLConverterTestCase(unittest.TestCase):
    """ test case for XML converter """

    def test_basic(self):
        pet, _ = _APP.resolve_obj('#/definitions/pet', from_spec_version='2.0')

        x = pet.properties['photoUrls'].xml
        obj = converters.to_xml(x, '')
        self.assertEqual(obj['name'], x.name)
        self.assertEqual(obj['wrapped'], x.wrapped)


class SchemaConverterTestCase(unittest.TestCase):
    """ test case for schema converter """

    def test_basic(self):
        pet, _ = _APP.resolve_obj('#/definitions/pet', from_spec_version='2.0')

        obj = converters.to_schema(pet, '')
        self.assertEqual(obj['required'], pet.required)
        _id = obj['properties']['id']
        self.assertEqual(_id['type'], 'integer')
        self.assertEqual(_id['format'], 'int64')
        _category = obj['properties']['category']
        self.assertEqual(_category['$ref'], '#/definitions/category')
        _photo_urls = obj['properties']['photoUrls']
        self.assertEqual(_photo_urls['type'], 'array')
        self.assertEqual(_photo_urls['items']['type'], 'string')
        _status = obj['properties']['status']
        self.assertEqual(
            sorted(_status['enum']), sorted(['available', 'pending', 'sold']))


class SecuritySchemeConverterTestCase(unittest.TestCase):
    """ test case for security scheme """

    def test_basic(self):
        auth, _ = _APP.resolve_obj(
            '#/securityDefinitions/petstore_auth', from_spec_version='2.0')

        obj = converters.to_security_scheme(auth, '')
        self.assertEqual(obj['type'], 'oauth2')
        flows = obj['flows']['implicit']
        self.assertEqual(flows['authorizationUrl'],
                         'http://petstore.swagger.io/api/oauth/dialog')
        self.assertTrue('write:pets' in flows['scopes'])
        self.assertTrue('read:pets' in flows['scopes'])


class HeaderConverterTestCase(unittest.TestCase):
    """ test case for header """

    def test_basic(self):
        header, _ = _APP.resolve_obj(
            '#/paths/~1p2/get/responses/200/headers/X-TEST',
            from_spec_version='2.0')

        obj = converters.to_header(header, '')
        self.assertEqual(obj['style'], 'simple')
        self.assertEqual(obj['schema']['type'], 'array')
        self.assertEqual(obj['schema']['items']['type'], 'string')


class ParameterConverterTestCase(unittest.TestCase):
    """ test case for parameter """

    def test_basic(self):
        param, _ = _APP.resolve_obj(
            '#/paths/~1p1/get/parameters/0', from_spec_version='2.0')

        obj, pctx = converters.from_parameter(param, None, [], '')
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
        self.assertEqual(
            sorted(_items['enum']), sorted(['available', 'pending', 'sold']))

    def test_file_in_form(self):
        param, _ = _APP.resolve_obj(
            '#/parameters/form_file', from_spec_version='2.0')

        obj, pctx = converters.from_parameter(
            param, None, ['application/x-www-form-urlencoded'], '')
        self.assertTrue(pctx.is_body)
        self.assertTrue(pctx.is_file)

        _schema = obj['content']['application/x-www-form-urlencoded']['schema'][
            'properties']['form_file']
        self.assertEqual(_schema['type'], 'string')
        self.assertEqual(_schema['format'], 'binary')

    def test_file_in_body(self):
        """ this is not a valid usage in 2.0, but someone suffer from that:
            https://github.com/OAI/OpenAPI-Specification/issues/1226
        """

        # normal body parameter with file type
        param, _ = _APP.resolve_obj(
            '#/parameters/body_file', from_spec_version='2.0')

        obj, pctx = converters.from_parameter(
            param, None, ['application/x-www-form-urlencoded'], '')
        self.assertTrue(pctx.is_body)
        self.assertTrue(pctx.is_file)
        _schema = obj['content']['application/x-www-form-urlencoded']['schema'][
            'properties']['body_file']
        self.assertEqual(_schema['type'], 'string')
        self.assertEqual(_schema['format'], 'binary')

        # body parameter with $ref to schema with file type
        param, _ = _APP.resolve_obj(
            '#/parameters/body_file_ref', from_spec_version='2.0')

        obj, pctx = converters.from_parameter(
            param, None, ['application/x-www-form-urlencoded'], '')
        self.assertTrue(pctx.is_body)
        self.assertTrue(pctx.is_file)
        _schema = obj['content']['application/x-www-form-urlencoded']['schema'][
            'properties']['body_file_ref']
        self.assertEqual(_schema['$ref'], '#/definitions/some_file')


class ResponseConverterTestCase(unittest.TestCase):
    """ test case for response """

    def test_basic(self):
        operation, _ = _APP.resolve_obj(
            '#/paths/~1p1/get', from_spec_version='2.0')
        obj = converters.to_response(operation.responses['200'],
                                     operation.produces, '')

        self.assertEqual(obj['description'], 'successful operation')
        self.assertTrue('content' in obj)
        _content = obj['content']
        self.assertTrue('application/json' in _content)
        self.assertTrue(_content['application/json']['schema']['items']['$ref'],
                        '#/components/schemas/pet')
        self.assertTrue(_content['application/json']['schema']['type'], 'array')

    def test_with_header(self):
        operation, _ = _APP.resolve_obj(
            '#/paths/~1p2/get', from_spec_version='2.0')
        obj = converters.to_response(operation.responses['200'], [], '')

        self.assertEqual(obj['description'], 'test for header')
        self.assertTrue('headers' in obj and 'X-TEST' in obj['headers'])
        _header = obj['headers']['X-TEST']
        self.assertEqual(_header['style'], 'simple')
        self.assertEqual(_header['schema']['items']['type'], 'string')
        self.assertEqual(_header['schema']['type'], 'array')

    def test_with_ref(self):
        operation, _ = _APP.resolve_obj(
            '#/paths/~1p4/post', from_spec_version='2.0')

        # without 'schema', just keep $ref
        obj = converters.to_response(operation.responses['default'],
                                     operation.produces,
                                     'test_response_default')
        self.assertEqual(obj['$ref'], '#/responses/void')

        # with 'schema', should inline it
        obj = converters.to_response(operation.responses['401'],
                                     operation.produces, 'test_response_401')
        self.assertEqual(obj['description'], 'unauthorized')
        self.assertTrue('application/json' in obj['content'])
        media = obj['content']['application/json']
        self.assertEqual(media['schema']['$ref'],
                         '#/definitions/generic_response')

        self.assertTrue('application/xml' in obj['content'])
        media = obj['content']['application/xml']
        self.assertEqual(media['schema']['$ref'],
                         '#/definitions/generic_response')

        # with 'schema', and without content-types as 'produces'
        obj = converters.to_response(operation.responses['401'],
                                     operation.produces, 'test_response_401')
        self.assertTrue('application/json' in obj['content'])
        media = obj['content']['application/json']
        self.assertEqual(media['schema']['$ref'],
                         '#/definitions/generic_response')


class OperationConverterTestCase(unittest.TestCase):
    """ test case for operation """

    def test_basic(self):
        operation, _ = _APP.resolve_obj(
            '#/paths/~1p1/get', from_spec_version='2.0')

        obj = converters.to_operation(operation, None, 'test_root', '')
        self.assertTrue('responses' in obj and '200' in obj['responses'])
        _response = obj['responses']['200']
        self.assertEqual(_response['description'], 'successful operation')
        self.assertTrue(
            'content' in _response
            and 'application/json' in _response['content']
            and 'schema' in _response['content']['application/json'])
        _schema = _response['content']['application/json']['schema']
        self.assertEqual(_schema['items']['$ref'], '#/definitions/pet')
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
        self.assertEqual(
            sorted(_schema['items']['enum']),
            sorted(['available', 'pending', 'sold']))
        self.assertEqual(_schema['items']['type'], 'string')

    def test_multiple_file(self):
        operation, _ = _APP.resolve_obj(
            '#/paths/~1p1/post', from_spec_version='2.0')
        obj = converters.to_operation(operation, None, 'test_root', '')

        # requestBody
        self.assertEqual(obj['requestBody']['required'], True)
        _media_type = obj['requestBody']['content']['multipart/form-data']
        _encoding = _media_type['encoding']
        self.assertEqual(_encoding['picture'],
                         {'contentType': 'application/octet-stream'})
        self.assertEqual(_encoding['description'],
                         {'contentType': 'text/plain'})
        self.assertEqual(_encoding['thumbnail'],
                         {'contentType': 'application/octet-stream'})
        _properties = _media_type['schema']['properties']
        self.assertEqual(_properties['picture'], {
            'type': 'string',
            'format': 'binary'
        })
        self.assertEqual(_properties['description'], {'type': 'string'})
        self.assertEqual(_properties['thumbnail'], {
            'type': 'string',
            'format': 'binary'
        })

        # response
        self.assertEqual(obj['responses']['200']['description'],
                         'successful operation')

    def test_parameter_ref(self):
        """ test parameters declared with '$ref'
        """
        operation, _ = _APP.resolve_obj(
            '#/paths/~1p2/post', from_spec_version='2.0')
        obj = converters.to_operation(operation, None, 'test_root', '')
        _content = obj['requestBody']['content']
        self.assertTrue('application/x-www-form-urlencoded' in _content)
        _properties = _content['application/x-www-form-urlencoded']['schema'][
            'properties']
        self.assertTrue('form_file' in _properties)
        self.assertEqual(_properties['form_file']['$ref'],
                         '#/parameters/form_file')
        self.assertTrue('description' in _properties)
        self.assertEqual(_properties['description']['$ref'],
                         '#/parameters/form_string')
        _encoding = _content['application/x-www-form-urlencoded']['encoding']
        self.assertTrue('form_file' in _encoding)
        self.assertEqual(_encoding['form_file']['contentType'],
                         'application/octet-stream')
        self.assertTrue('description' in _encoding)
        self.assertEqual(_encoding['description']['contentType'], 'text/plain')

        _parameter = obj['parameters'][0]
        self.assertEqual(_parameter['$ref'], '#/parameters/query_string')


class InfoConverterTestCase(unittest.TestCase):
    """ test case for info """

    def test_basic(self):
        info, _ = _APP.resolve_obj('#/info', from_spec_version='2.0')

        obj = converters.to_info(info, '')
        self.assertEqual(obj['title'], 'Swagger Petstore')
        self.assertEqual(obj['version'], '1.0.0')
        self.assertEqual(obj['termsOfService'], 'http://helloreverb.com/terms/')
        self.assertEqual(obj['description'],
                         'This is a sample server Petstore server.')
        _license = obj['license']
        self.assertEqual(_license['url'],
                         'http://www.apache.org/licenses/LICENSE-2.0.html')
        self.assertEqual(_license['name'], 'Apache 2.0')
        _contact = obj['contact']
        self.assertEqual(_contact['email'], 'apiteam@wordnik.com')


class PathItemConverterTestCase(unittest.TestCase):
    """ test case for path item """

    def test_basic(self):
        path_item, _ = _APP.resolve_obj('#/paths/~1p1', from_spec_version='2.0')

        obj, reloc = converters.to_path_item(path_item, 'test_root', '')
        self.assertTrue('get' in obj)
        self.assertTrue('post' in obj)
        self.assertFalse('options' in obj)

        self.assertEqual(reloc, {})

    def test_path_item_parameters(self):
        """ make sure PathItem.parameters are correctly handled:

            - request-body: inline all 'body' or 'file' parameter
            to each operation
            - other parameter: let them stay in PathItem.parameters
        """
        path_item, _ = _APP.resolve_obj(
            '#/paths/~1p3~1{user_name}', from_spec_version='2.0')

        obj, reloc = converters.to_path_item(path_item, 'test_root', '')
        self.assertTrue('post' in obj)
        _post = obj['post']
        self.assertFalse('parameters' in _post)

        self.assertTrue('requestBody' in _post)
        media = _post['requestBody']['content']['multipart/form-data']
        self.assertTrue('encoding' in media)
        self.assertEqual(media['encoding']['form_file']['contentType'],
                         'application/octet-stream')
        self.assertTrue('schema' in media)
        self.assertEqual(media['schema']['properties']['form_file']['$ref'],
                         '#/parameters/form_file')

        media = _post['requestBody']['content'][
            'application/x-www-form-urlencoded']
        self.assertTrue('encoding' in media)
        self.assertEqual(media['encoding']['description']['contentType'],
                         'text/plain')
        self.assertTrue('schema' in media)
        self.assertEqual(media['schema']['required'], ['description'])
        self.assertEqual(media['schema']['properties']['description']['$ref'],
                         '#/parameters/form_string')

        self.assertTrue('parameters' in obj)
        _parameters = obj['parameters']
        for param in _parameters:
            if '$ref' in param:
                self.assertEqual(param['$ref'], '#/parameters/query_string')
            elif 'name' in param:
                self.assertEqual(param['name'], 'user_name')
            else:
                self.assertTrue(False)

        # check object relocation
        self.assertEqual(reloc['parameters/0'],
                         'x-pyopenapi_internal_request_body')
        self.assertEqual(reloc['parameters/1'],
                         'x-pyopenapi_internal_request_body')


class ServerTestCase(unittest.TestCase):
    """ test case for server """

    def test_from_swagger(self):
        obj = converters.from_swagger_to_server(_APP.root, '')

        self.assertTrue('url' in obj)
        self.assertEqual(obj['url'], '/')


class OpenAPITestCase(unittest.TestCase):
    """ test case for OpenAPI """

    @classmethod
    def setUpClass(cls):
        cls.from_upgrade, cls.upgrade_reloc = converters.to_openapi(
            _APP.root, '')

    def test_basic(self):
        obj = self.from_upgrade

        self.assertTrue('info' in obj)
        self.assertTrue('servers' in obj)

        self.assertTrue('paths' in obj)
        _paths = obj['paths']
        self.assertTrue('/p1' in _paths)
        self.assertTrue('/p2' in _paths)

        self.assertTrue('components' in obj)
        _components = obj['components']
        self.assertTrue('securitySchemes' in _components)
        self.assertTrue('schemas' in _components)

        self.assertTrue('externalDocs' in obj)

    def test_reloc(self):
        """ make sure the object relocation map is correct
        """
        reloc = self.upgrade_reloc
        self.assertEqual(reloc['paths']['~1p3~1{user_name}']['parameters/0'],
                         'x-pyopenapi_internal_request_body')
        self.assertEqual(reloc['paths']['~1p3~1{user_name}']['parameters/1'],
                         'x-pyopenapi_internal_request_body')

        self.assertEqual(reloc['securityDefinitions'],
                         'components/securitySchemes')
        self.assertEqual(reloc['responses'], 'components/responses')
        self.assertEqual(reloc['definitions'], 'components/schemas')

        self.assertEqual(reloc['parameters'][''], '#/components/parameters')
        self.assertEqual(reloc['parameters']['body_ref_pet'],
                         '#/components/requestBodies/body_ref_pet')
        self.assertEqual(reloc['parameters']['form_string'],
                         '#/components/requestBodies/form_string')
        self.assertEqual(reloc['parameters']['body_file_ref'],
                         '#/components/requestBodies/body_file_ref')
        self.assertEqual(reloc['parameters']['body_obj_simple'],
                         '#/components/requestBodies/body_obj_simple')
        self.assertEqual(reloc['parameters']['body_file'],
                         '#/components/requestBodies/body_file')
        self.assertEqual(reloc['parameters']['form_file'],
                         '#/components/requestBodies/form_file')

    def test_request_bodies(self):
        """ make sure we create requestBodies with
        reasonable content types
        """

        _request_bodies = self.from_upgrade['components']['requestBodies']

        _form_file = _request_bodies['form_file']
        self.assertTrue('multipart/form-data' in _form_file['content'])

        _body_file = _request_bodies['body_file']
        self.assertTrue('multipart/form-data' in _body_file['content'])

        _body_file_ref = _request_bodies['body_file_ref']
        self.assertTrue('multipart/form-data' in _body_file_ref['content'])

        _form_string = _request_bodies['form_string']
        self.assertTrue(
            'application/x-www-form-urlencoded' in _form_string['content'])

        _body_obj_simple = _request_bodies['body_obj_simple']
        self.assertTrue('application/json' in _body_obj_simple['content'])
        _schema_properties = _body_obj_simple['content']['application/json'][
            'schema']['properties']
        self.assertTrue('phone' in _schema_properties)
        self.assertEqual(_schema_properties['phone']['type'], 'string')
        self.assertTrue('email' in _schema_properties)
        self.assertEqual(_schema_properties['email']['type'], 'string')

        _body_ref_pet = _request_bodies['body_ref_pet']
        self.assertTrue('application/json' in _body_ref_pet['content'])
        _schema = _body_ref_pet['content']['application/json']['schema']
        self.assertEqual(_schema['$ref'], '#/definitions/pet')
