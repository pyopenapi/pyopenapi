import unittest
import os

from pyopenapi import errs
from pyopenapi.utils import normalize_url
from pyopenapi.migration.versions.v2_0 import objects
from ....utils import get_test_data_folder, SampleApp

_FOLDER = normalize_url(get_test_data_folder(version='1.2', which='wordnik'))


def _patch_folder(path_):
    return _FOLDER + '#' + path_


class SwaggerUpgradeTestCase(unittest.TestCase):
    """ test for upgrade from converting 1.2 to 2.0 """

    @classmethod
    def setUpClass(cls):
        cls.app = SampleApp.create(
            _FOLDER,
            to_spec_version='2.0',
        )

    def test_resource_list(self):
        """ ResourceList -> Swagger
        """
        obj = self.app.root

        self.assertEqual(obj.swagger, '2.0')
        self.assertEqual(obj.host, 'petstore.swagger.wordnik.com')
        self.assertEqual(obj.basePath, '')
        self.assertEqual(obj.info.version, '1.0.0')
        self.assertEqual(obj.schemes, ['http', 'https'])
        self.assertEqual(obj.consumes, [])
        self.assertEqual(obj.produces, [])

    def test_resource(self):
        """  Resource -> Tag, Operation
        make sure the way we rearrange resources
        to tags is correct.
        """
        obj = self.app.root
        self.assertEqual(
            sorted([t.name for t in obj.tags]), sorted(['store', 'user',
                                                        'pet']))

        path_items = self.app.root.paths
        self.assertEqual(
            sorted(path_items.keys()),
            sorted([
                '/api/user/createWithArray', '/api/store/order',
                '/api/user/login', '/api/user', '/api/pet',
                '/api/pet/findByTags', '/api/pet/findByStatus',
                '/api/store/order/{orderId}', '/api/user/logout',
                '/api/pet/uploadImage', '/api/user/createWithList',
                '/api/user/{username}', '/api/pet/{petId}'
            ]))

    def test_operation(self):
        """ Operation -> Operation
        """
        path_item = self.app.root.paths['/api/pet/{petId}']

        # getPetById
        operation = path_item.get
        self.assertEqual(operation.tags, ['pet'])
        self.assertEqual(operation.operationId, 'getPetById')
        self.assertEqual(
            operation.produces,
            ['application/json', 'application/xml', 'text/plain', 'text/html'])
        self.assertEqual(operation.consumes, None)
        self.assertEqual(operation.summary, 'Find pet by ID')
        self.assertEqual(operation.description, 'Returns a pet based on ID')
        self.assertEqual(operation.deprecated, False)

        # partialUpdate
        operation = path_item.patch
        self.assertEqual(operation.produces,
                         ['application/json', 'application/xml'])
        self.assertEqual(operation.consumes,
                         ['application/json', 'application/xml'])
        self.assertEqual(operation.security, [{'oauth2': ['write:pets']}])
        self.assertTrue('default' in operation.responses)

        resp = operation.responses['default']
        self.assertEqual(resp.headers, None)
        self.assertEqual(resp.schema.type, 'array')
        self.assertEqual(
            resp.schema.items.get_attrs('migration').normalized_ref,
            _patch_folder('/definitions/pet!##!Pet'))

        # createUser
        operation = self.app.root.paths['/api/user'].post
        self.assertEqual(operation.tags, ['user'])
        self.assertEqual(operation.operationId, 'createUser')

    def test_authorization(self):
        """ Authorization -> Security Scheme
        """
        sec = self.app.root.securityDefinitions
        self.assertEqual(list(sec.keys()), ['oauth2'])

        scheme = sec['oauth2']
        self.assertEqual(scheme.type, 'oauth2')
        self.assertEqual(scheme.name, None)
        self.assertEqual(getattr(scheme, 'in'), None)
        self.assertEqual(scheme.flow, 'implicit')
        self.assertEqual(scheme.authorizationUrl,
                         'http://petstore.swagger.wordnik.com/api/oauth/dialog')
        self.assertEqual(scheme.tokenUrl,
                         'http://petstore.swagger.wordnik.com/api/oauth/token')
        self.assertEqual(
            scheme.scopes, {
                'write:pets': 'Modify pets in your account',
                'read:pets': 'Read your pets'
            })

    def test_parameter(self):
        """ Parameter -> Parameter
        """
        # body
        operation = self.app.root.paths['/api/pet/{petId}'].patch
        body = [x for x in operation.parameters
                if getattr(x, 'in') == 'body'][0]
        self.assertEqual(getattr(body, 'in'), 'body')
        self.assertEqual(body.required, True)
        self.assertEqual(
            body.schema.get_attrs('migration').normalized_ref,
            _patch_folder('/definitions/pet!##!Pet'))

        # form
        operation = self.app.root.paths['/api/pet/uploadImage'].post
        form = [
            x for x in operation.parameters
            if getattr(x, 'in') == 'formData' and x.type == 'string'
        ][0]
        self.assertEqual(form.name, 'additionalMetadata')
        self.assertEqual(form.required, False)

        # file
        operation = self.app.root.paths['/api/pet/uploadImage'].post
        file_ = [
            x for x in operation.parameters
            if getattr(x, 'in') == 'formData' and x.type == 'file'
        ][0]
        self.assertEqual(file_.name, 'file')
        self.assertEqual(file_.required, False)

        # non-body can't have $ref
        try:
            SampleApp.create(
                get_test_data_folder(version='1.2', which='upgrade_parameter'),
                to_spec_version='2.0')
        except errs.SchemaError as e:
            self.assertEqual(e.args,
                             ("Can't have $ref in non-body Parameters", ))
        else:
            self.fail('SchemaError not raised')

    def test_model(self):
        """ Model -> Definition
        """
        schema = self.app.root.definitions['pet!##!Pet']
        self.assertEqual(schema.required, ['id', 'name'])

        property_names = schema.properties.keys()
        self.assertEqual(
            sorted(property_names),
            ['category', 'id', 'name', 'photoUrls', 'status', 'tags'])

        prop = schema.properties['id']
        self.assertEqual(prop.type, 'integer')
        self.assertEqual(prop.format, 'int64')
        self.assertEqual(prop.description, 'unique identifier for the pet')
        self.assertEqual(prop.minimum, 0)
        self.assertEqual(prop.maximum, 100)

        prop = schema.properties['category']
        self.assertEqual(
            prop.get_attrs('migration').normalized_ref,
            _patch_folder('/definitions/pet!##!Category'))

        prop = schema.properties['photoUrls']
        self.assertEqual(prop.type, 'array')
        self.assertEqual(prop.items.type, 'string')

        prop = schema.properties['tags']
        self.assertEqual(prop.type, 'array')
        self.assertEqual(
            prop.items.get_attrs('migration').normalized_ref,
            _patch_folder('/definitions/pet!##!Tag'))

        prop = schema.properties['status']
        self.assertEqual(prop.type, 'string')
        self.assertEqual(prop.enum, ['available', 'pending', 'sold'])

    def test_item(self):
        """ make sure to raise exception for invalid item
        """
        try:
            SampleApp.create(
                get_test_data_folder(
                    version='1.2',
                    which=os.path.join('upgrade_items', 'with_ref')),
                to_spec_version='2.0')
        except errs.SchemaError as e:
            self.assertEqual(e.args, ('Can\'t have $ref for Items', ))
        else:
            self.fail('SchemaError not raised')

        try:
            SampleApp.create(
                get_test_data_folder(
                    version='1.2',
                    which=os.path.join('upgrade_items', 'invalid_primitive')),
                to_spec_version='2.0')
        except errs.SchemaError as e:
            self.assertEqual(e.args,
                             ('Non primitive type is not allowed for Items', ))
        else:
            self.fail('SchemaError not raised')

    def test_info(self):
        """ Info -> [Info, Contact, License]
        """
        info = self.app.root.info
        self.assertEqual(info.title, 'Swagger Sample App')
        self.assertEqual(
            info.description,
            'This is a sample server Petstore server.  You can find out more about Swagger \n    at <a href=\"http://swagger.wordnik.com\">http://swagger.wordnik.com</a> or on irc.freenode.net, #swagger.  For this sample,\n    you can use the api key \"special-key\" to test the authorization filters'
        )
        self.assertEqual(info.termsOfService, 'http://helloreverb.com/terms/')
        self.assertTrue(isinstance(info.license, objects.License))
        self.assertEqual(info.license.name, 'Apache 2.0')
        self.assertEqual(info.license.url,
                         'http://www.apache.org/licenses/LICENSE-2.0.html')
        self.assertTrue(isinstance(info.contact, objects.Contact))
        self.assertEqual(info.contact.email, 'apiteam@wordnik.com')

    def test_authorizations(self):
        """ Authorizations -> [Security Requirement]
        """


class ModelSubtypesTestCase(unittest.TestCase):
    """ test for upgrade /data/v1_2/model_subtypes """

    @classmethod
    def setUpClass(cls):
        cls.app = SampleApp.create(
            get_test_data_folder(version='1.2', which='model_subtypes'),
            to_spec_version='2.0')

    def test_path_item(self):
        paths, _ = self.app.resolve_obj('#/paths', '1.2', to_spec_version='2.0')
        self.assertEqual(
            sorted(list(paths.keys())),
            sorted(['/api/user', '/api/user/{username}']))
