# -*- coding: utf-8 -*-
import os
import json
import unittest

from pyopenapi.utils import compare_container
from pyopenapi.migration.versions.v2_0.objects import Swagger
from ....utils import get_test_data_folder, SampleApp


class ConverterTestCase(unittest.TestCase):
    """ test for converter """

    def test_v2_0(self):
        """ convert from 2.0 to 2.0 """
        path = get_test_data_folder(version='2.0', which='wordnik')
        app = SampleApp.create(path, to_spec_version='2.0')

        # load swagger.json into dict
        origin = None
        with open(os.path.join(path, 'swagger.json')) as handle:
            origin = json.loads(handle.read())

        # diff for empty list or dict is allowed
        dumped = app.root.dump()
        self.assertEqual(
            sorted(compare_container(origin, dumped)),
            sorted([('paths/~1store~1inventory/get/parameters', None, None),
                    ('paths/~1user~1logout/get/parameters', None, None)]))

        # try to load the dumped dict back, to see if anything wrong
        Swagger(dumped)


# pylint: disable=invalid-name
class Converter_v1_2_TestCase(unittest.TestCase):
    """ test for convert from 1.2

        Not converted:
        - Response Message Object
        - Token Request Endpoint Object
        - API Object
        - Resource Object
    """

    @classmethod
    def setUpClass(cls):
        cls.app = SampleApp.create(
            get_test_data_folder(version='1.2', which='wordnik'),
            sep=':',
            to_spec_version='2.0',
        )

    def test_items(self):
        """
        """
        # $ref
        expect = {'$ref': '#/definitions/pet:Pet'}
        target, _ = self.app.resolve_obj(
            '#/paths/~1api~1pet~1{petId}/patch/responses/default/schema/items',
            from_spec_version='2.0',
        )
        self.assertEqual(compare_container(expect, target.dump()), [])

        # enum
        expect = {
            'enum': ['available', 'pending', 'sold'],
            'type': 'string',
        }
        target, _ = self.app.resolve_obj(
            '#/paths/~1api~1pet~1findByStatus/get/parameters/0/items',
            from_spec_version='2.0',
        )
        self.assertEqual(compare_container(expect, target.dump()), [])

        # type
        expect = {'type': 'string'}
        target, _ = self.app.resolve_obj(
            '#/definitions/pet:Pet/properties/photoUrls/items',
            from_spec_version='2.0',
        )
        self.assertEqual(compare_container(expect, target.dump()), [])

    def test_scope(self):
        """
        """
        # test scope in Swagger Object
        expect = {
            'write:pets': 'Modify pets in your account',
            'read:pets': 'Read your pets',
        }
        self.assertEqual(
            compare_container(
                expect,
                self.app.root.securityDefinitions['oauth2'].scopes.dump()), [])

        # test scope in Operation Object
        expect = [dict(oauth2=['write:pets'])]
        target, _ = self.app.resolve_obj(
            '#/paths/~1api~1store~1order~1{orderId}/delete/security',
            from_spec_version='2.0',
        )
        self.assertEqual(compare_container(expect, target.dump()), [])

    def test_login_endpoint(self):
        """
        """
        expect = {
            'authorizationUrl':
            "http://petstore.swagger.wordnik.com/api/oauth/dialog",
        }

        self.assertEqual(
            compare_container(
                expect,
                self.app.root.securityDefinitions['oauth2'].dump(),
                include=['authorizationUrl']), [])

    def test_implicit(self):
        """
        """
        expect = {
            'type':
            'oauth2',
            'authorizationUrl':
            "http://petstore.swagger.wordnik.com/api/oauth/dialog",
            'flow':
            'implicit'
        }

        self.assertEqual(
            compare_container(
                expect,
                self.app.root.securityDefinitions['oauth2'].dump(),
                include=['type', 'authorizationUrl', 'flow']), [])

    def test_authorizations(self):
        """
        """
        expect = [dict(oauth2=['write:pets'])]
        target, _ = self.app.resolve_obj(
            '#/paths/~1api~1store~1order/post/security',
            from_spec_version='2.0',
        )
        self.assertEqual(compare_container(expect, target.dump()), [])

    def test_authorization(self):
        """
        """
        expect = {
            'authorizationUrl':
            'http://petstore.swagger.wordnik.com/api/oauth/dialog',
            'tokenUrl':
            'http://petstore.swagger.wordnik.com/api/oauth/token',
            'type':
            'oauth2',
            'flow':
            'implicit',
        }

        self.assertEqual(
            compare_container(
                expect,
                self.app.root.securityDefinitions['oauth2'].dump(),
                exclude=[
                    'scopes',
                ]), [])

    def test_parameter(self):
        """
        """
        expect = {
            'name': 'petId',
            'description': 'ID of pet that needs to be fetched',
            'required': True,
            'type': 'integer',
            'format': 'int64',
            'minimum': 1.0,
            'maximum': 100000.0,
            'in': 'path',
        }
        target, _ = self.app.resolve_obj(
            '#/paths/~1api~1pet~1{petId}/get/parameters/0',
            from_spec_version='2.0',
        )
        self.assertEqual(compare_container(expect, target.dump()), [])

        # allowMultiple, defaultValue, enum
        expect = {
            'default': ['available'],
            'items': {
                'type': 'string',
                'enum': ['available', 'pending', 'sold']
            },
            'collectionFormat': 'csv',
        }
        target, _ = self.app.resolve_obj(
            '#/paths/~1api~1pet~1findByStatus/get/parameters/0',
            from_spec_version='2.0',
        )
        self.assertEqual(
            compare_container(
                expect,
                target.dump(),
                include=['collectionFormat', 'default', 'enum']), [])

        # $ref, or Model as type
        expect = {'in': 'body', 'schema': {'$ref': '#/definitions/pet:Pet'}}
        target, _ = self.app.resolve_obj(
            '#/paths/~1api~1pet/post/parameters/0',
            from_spec_version='2.0',
        )
        self.assertEqual(
            compare_container(expect, target.dump(), include=['schema', 'in']),
            [])

    def test_operation(self):
        """
        """
        expect = {
            'operationId': 'getPetById',
            'summary': 'Find pet by ID',
            'description': 'Returns a pet based on ID',
        }
        target, _ = self.app.resolve_obj(
            '#/paths/~1api~1pet~1{petId}/get',
            from_spec_version='2.0',
        )
        self.assertEqual(
            compare_container(
                expect,
                target.dump(),
                include=['operationId', 'summary', 'description']), [])

        # produces, consumes
        expect = {
            'produces': ['application/json', 'application/xml'],
            'consumes': ['application/json', 'application/xml']
        }
        target, _ = self.app.resolve_obj(
            '#/paths/~1api~1pet~1{petId}/patch',
            from_spec_version='2.0',
        )
        self.assertEqual(
            compare_container(
                expect, target.dump(), include=['produces', 'consumes']), [])

        # deprecated
        expect = dict(deprecated=True)
        target, _ = self.app.resolve_obj(
            '#/paths/~1api~1pet~1findByTags/get',
            from_spec_version='2.0',
        )
        self.assertEqual(
            compare_container(expect, target.dump(), include=['deprecated']),
            [])

        # responses, in 1.2, the type of Operation is default response
        expect = {
            'schema': {
                'type': 'array',
                'items': {
                    '$ref': '#/definitions/pet:Pet',
                }
            },
            'description': '',
        }
        target, _ = self.app.resolve_obj(
            '#/paths/~1api~1pet~1findByTags/get/responses/default',
            from_spec_version='2.0',
        )
        self.assertEqual(
            compare_container(expect, target.dump(), exclude=['$ref']), [])

    def test_property(self):
        """
        """
        expect = {
            "type": "integer",
            "format": "int32",
            "description": "User Status",
            "enum": ["1-registered", "2-active", "3-closed"]
        }
        target, _ = self.app.resolve_obj(
            '#/definitions/user:User/properties/userStatus',
            from_spec_version='2.0',
        )
        self.assertEqual(compare_container(expect, target.dump()), [])

    def test_model(self):
        """
        """
        expect = {
            "required": ["id", "name"],
            "properties": {
                "id": {
                    "type": "integer",
                    "format": "int64",
                    "description": "unique identifier for the pet",
                    "minimum": 0,
                    "maximum": 100.0
                },
                "category": {
                    "$ref": "#/definitions/pet:Category"
                },
                "name": {
                    "type": "string"
                },
                "photoUrls": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "tags": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/pet:Tag"
                    }
                },
                "status": {
                    "type": "string",
                    "description": "pet status in the store",
                    "enum": ["available", "pending", "sold"]
                }
            }
        }
        target, _ = self.app.resolve_obj(
            '#/definitions/pet:Pet',
            from_spec_version='2.0',
        )
        self.assertEqual(
            compare_container(expect, target.dump(), exclude=['$ref']), [])

    def test_info(self):
        """
        """
        expect = dict(
            version='1.0.0',
            title='Swagger Sample App',
            description=
            'This is a sample server Petstore server.  You can find out more about Swagger \n    at <a href=\"http://swagger.wordnik.com\">http://swagger.wordnik.com</a> or on irc.freenode.net, #swagger.  For this sample,\n    you can use the api key \"special-key\" to test the authorization filters',
            termsOfService='http://helloreverb.com/terms/',
            contact=dict(email='apiteam@wordnik.com'),
            license=dict(
                name='Apache 2.0',
                url='http://www.apache.org/licenses/LICENSE-2.0.html'))
        self.assertEqual(
            compare_container(self.app.root.info.dump(), expect), [])

    def test_resource_list(self):
        """
        """
        expect = dict(swagger='2.0')
        self.assertEqual(
            compare_container(
                expect, self.app.root.dump(), include=['swagger']), [])


# pylint: disable=invalid-name
class Converter_v1_2_TestCase_Others(unittest.TestCase):
    """ for test cases needs special init
    """

    def test_token_endpoint(self):
        """
        """
        app = SampleApp.create(
            get_test_data_folder(version='1.2', which='simple_auth'),
            to_spec_version='2.0',
        )

        expect = {
            'tokenUrl': 'http://petstore.swagger.wordnik.com/api/oauth/token',
            'type': 'oauth2',
            'flow': 'access_code',
            'scopes': {
                'test:anything': 'for testing purpose'
            }
        }
        target, _ = app.resolve_obj(
            '#/securityDefinitions/oauth2',
            from_spec_version='2.0',
        )
        self.assertEqual(compare_container(expect, target.dump()), [])

    def test_authorization(self):
        """
        """
        app = SampleApp.create(
            get_test_data_folder(version='1.2', which='simple_auth'),
            to_spec_version='2.0',
        )

        expect = {'type': 'apiKey', 'in': 'query', 'name': 'simpleQK'}
        target, _ = app.resolve_obj(
            '#/securityDefinitions/simple_key',
            from_spec_version='2.0',
        )
        self.assertEqual(compare_container(expect, target.dump()), [])

        expect = {'type': 'apiKey', 'in': 'header', 'name': 'simpleHK'}
        target, _ = app.resolve_obj(
            '#/securityDefinitions/simple_key2',
            from_spec_version='2.0',
        )
        self.assertEqual(compare_container(expect, target.dump()), [])

        expect = {
            'type': 'basic',
        }
        target, _ = app.resolve_obj(
            '#/securityDefinitions/simple_basic',
            from_spec_version='2.0',
        )
        self.assertEqual(compare_container(expect, target.dump()), [])

    def test_model_inheritance(self):
        """
        """
        app = SampleApp.create(
            get_test_data_folder(version='1.2', which='model_subtypes'),
            to_spec_version='2.0',
            sep=':')

        expect = {'allOf': [{'$ref': u'#/definitions/user:User'}]}
        target, _ = app.resolve_obj(
            '#/definitions/user:UserWithInfo',
            from_spec_version='2.0',
        )
        self.assertEqual(
            compare_container(expect, target.dump(), include=['allOf']), [])
