import unittest

import six

from pyopenapi.migration.versions.v1_2.objects import (
    Info, Authorization, Scope, Items, GrantTypes, Implicit, AuthorizationCode,
    LoginEndpoint, TokenRequestEndpoint, TokenEndpoint, ApiDeclaration,
    ResourceInListing, Operation, Parameter, ResponseMessage, Authorizations,
    Model)
from ....utils import get_test_data_folder, SampleApp


class PropertyTestCase(unittest.TestCase):
    """ make sure properties' existence & type """

    @classmethod
    def setUpClass(kls):
        kls.app = SampleApp.create(
            get_test_data_folder(version='1.2', which='wordnik'),
            to_spec_version='2.0')

    def test_resource_list(self):
        """ resource list """
        self.assertTrue(isinstance(self.app.raw.info, Info))
        self.assertEqual(self.app.raw.info.title, 'Swagger Sample App')
        self.assertEqual(self.app.raw.swaggerVersion, '1.2')

    def test_authorizations(self):
        """ authorizations """
        self.assertTrue('oauth2' in self.app.raw.authorizations)
        self.assertTrue(
            isinstance(self.app.raw.authorizations['oauth2'], Authorization))
        self.assertEqual(self.app.raw.authorizations['oauth2'].type, 'oauth2')

    def test_scope(self):
        """ scope """
        auth = self.app.raw.authorizations['oauth2']
        self.assertEqual(len(auth.scopes), 2)
        self.assertTrue(isinstance(auth.scopes[0], Scope))
        self.assertTrue(isinstance(auth.scopes[0], Scope))
        self.assertEqual(auth.scopes[0].scope, 'write:pets')
        self.assertEqual(auth.scopes[1].scope, 'read:pets')
        self.assertEqual(auth.scopes[1].description, 'Read your pets')

    def test_grant_types(self):
        """ grant types """
        auth = self.app.raw.authorizations['oauth2']
        self.assertTrue(isinstance(auth.grantTypes, GrantTypes))

    def test_implicit(self):
        """ implicit """
        grant = self.app.raw.authorizations['oauth2'].grantTypes
        self.assertTrue(isinstance(grant.implicit, Implicit))
        self.assertEqual(grant.implicit.tokenName, 'access_token')

    def test_login_endpoint(self):
        """ login endpoint """
        implicit = self.app.raw.authorizations['oauth2'].grantTypes.implicit
        self.assertTrue(isinstance(implicit.loginEndpoint, LoginEndpoint))
        self.assertEqual(implicit.loginEndpoint.url,
                         'http://petstore.swagger.wordnik.com/api/oauth/dialog')

    def test_authorization_code(self):
        """ authorization code """
        grant = self.app.raw.authorizations['oauth2'].grantTypes
        self.assertTrue(isinstance(grant.authorization_code, AuthorizationCode))

    def test_token_request_endpoint(self):
        """ token request endpoint """
        auth = self.app.raw.authorizations[
            'oauth2'].grantTypes.authorization_code
        self.assertTrue(
            isinstance(auth.tokenRequestEndpoint, TokenRequestEndpoint))
        self.assertEqual(
            auth.tokenRequestEndpoint.url,
            'http://petstore.swagger.wordnik.com/api/oauth/requestToken')
        self.assertEqual(auth.tokenRequestEndpoint.clientIdName, 'client_id')
        self.assertEqual(auth.tokenRequestEndpoint.clientSecretName,
                         'client_secret')

    def test_token_endpoint(self):
        """ token endpoint """
        auth = self.app.raw.authorizations[
            'oauth2'].grantTypes.authorization_code
        self.assertTrue(isinstance(auth.tokenEndpoint, TokenEndpoint))
        self.assertEqual(auth.tokenEndpoint.url,
                         'http://petstore.swagger.wordnik.com/api/oauth/token')
        self.assertEqual(auth.tokenEndpoint.tokenName, 'auth_code')

    def test_resource_pet(self):
        """ resource """
        pet = self.app.raw.cached_apis['pet']
        self.assertTrue(isinstance(pet, ApiDeclaration))
        self.assertEqual(pet.swaggerVersion, '1.2')
        self.assertEqual(pet.apiVersion, '1.0.0')
        self.assertEqual(pet.basePath,
                         'http://petstore.swagger.wordnik.com/api')
        self.assertEqual(pet.resourcePath, '/pet')
        self.assertTrue('application/json' in pet.produces)
        self.assertTrue('application/xml' in pet.produces)
        self.assertTrue('text/plain' in pet.produces)
        self.assertTrue('text/html' in pet.produces)

    def test_operation(self):
        """ operation """
        pet = self.app.raw.cached_apis['pet']

        # find each operation's nickname
        nick_names = []
        for api in pet.apis:
            nick_names.extend([op.nickname for op in api.operations])

        self.assertEqual(
            sorted(nick_names),
            sorted([
                'updatePet', 'addPet', 'findPetsByStatus', 'findPetsByTags',
                'partialUpdate', 'updatePetWithForm', 'deletePet', 'getPetById',
                'uploadFile'
            ]))

        update_pet = pet.apis[1].operations[1]
        # make sure we locate the right operation to test
        self.assertEqual(update_pet.nickname, 'updatePet')

        self.assertTrue(isinstance(update_pet, Operation))
        self.assertEqual(update_pet.method, 'PUT')
        self.assertEqual(update_pet.summary, 'Update an existing pet')
        self.assertEqual(update_pet.notes, '')

    def test_parameter(self):
        """ parameter """
        update_pet = self.app.raw.cached_apis['pet'].apis[1].operations[1]
        # make sure we locate the right operation to test
        self.assertEqual(update_pet.nickname, 'updatePet')

        param = update_pet.parameters[0]
        self.assertTrue(isinstance(param, Parameter))
        self.assertEqual(param.paramType, 'body')
        self.assertEqual(param.name, 'body')
        self.assertEqual(param.required, True)
        self.assertEqual(param.allowMultiple, False)
        self.assertEqual(param.description,
                         'Pet object that needs to be updated in the store')

    def test_response_message(self):
        """ response message """
        update_pet = self.app.raw.cached_apis['pet'].apis[1].operations[1]
        msg = update_pet.responseMessages[0]
        self.assertTrue(isinstance(msg, ResponseMessage))
        self.assertEqual(msg.code, 400)
        self.assertEqual(msg.message, 'Invalid ID supplied')

    def test_model(self):
        """ model """
        pet = self.app.raw.cached_apis['pet'].models['Pet']
        self.assertTrue(isinstance(pet, Model))
        self.assertEqual(pet.id, 'Pet')
        self.assertEqual(sorted(pet.required), sorted(['id', 'name']))

    def test_authorization(self):
        """ authorization """
        # make sure we locate the expected operation
        operation = self.app.raw.cached_apis['pet'].apis[0].operations[2]
        self.assertEqual(operation.nickname, 'partialUpdate')

        auth = operation.authorizations['oauth2'][0]
        self.assertTrue(isinstance(auth, Authorizations))
        self.assertEqual(auth.scope, 'write:pets')

    def test_parent(self):
        """ make sure parent is assigned """
        self.assertTrue(self.app.raw.cached_apis['pet'].models['Pet']
                        ._parent_._parent_ is self.app.raw.cached_apis['pet'])

        get_user_by_name = self.app.raw.cached_apis['user'].apis[0].operations[
            2]
        self.assertEqual(get_user_by_name.nickname, 'getUserByName')
        self.assertTrue(get_user_by_name._parent_._parent_._parent_._parent_ is
                        self.app.raw.cached_apis['user'])

        self.assertTrue(self.app.raw.info._parent_ is self.app.raw)


class DataTypeTestCase(unittest.TestCase):
    """ make sure data type ready """

    @classmethod
    def setUpClass(kls):
        kls.app = SampleApp.create(
            get_test_data_folder(version='1.2', which='wordnik'),
            to_spec_version='2.0')

    def test_operation(self):
        """ operation """
        operation = self.app.raw.cached_apis['pet'].apis[2].operations[0]
        self.assertEqual(operation.nickname, 'findPetsByStatus')
        self.assertEqual(operation.type, 'array')
        self.assertEqual(getattr(operation.items, '$ref'), 'Pet')

    def test_parameter(self):
        """ parameter """
        operation = self.app.raw.cached_apis['pet'].apis[2].operations[0]
        self.assertEqual(operation.nickname, 'findPetsByStatus')

        param = operation.parameters[0]
        self.assertTrue(isinstance(param, Parameter))
        self.assertEqual(param.required, True)
        self.assertEqual(param.defaultValue, 'available')
        self.assertEqual(param.type, 'string')
        self.assertTrue(isinstance(param.enum, list))
        self.assertEqual(
            sorted(param.enum), sorted(['available', 'pending', 'sold']))

    def test_property(self):
        """ property """
        prop = self.app.raw.cached_apis['pet'].models['Pet'].properties
        # id
        self.assertEqual(prop['id'].type, 'integer')
        self.assertEqual(prop['id'].format, 'int64')
        # we are not convert to real type here,
        # this case is handled by Upgrading from 1.2 to 2.0
        self.assertEqual(prop['id'].minimum, '0.0')
        self.assertEqual(prop['id'].maximum, '100.0')
        # category
        self.assertEqual(getattr(prop['category'], '$ref'), 'Category')
        # name
        self.assertEqual(prop['name'].type, 'string')
        # photoUrls
        self.assertEqual(prop['photoUrls'].type, 'array')
        self.assertTrue(isinstance(prop['photoUrls'].items, Items))
        self.assertEqual(prop['photoUrls'].items.type, 'string')
        # tag
        self.assertEqual(prop['tags'].type, 'array')
        self.assertTrue(isinstance(prop['tags'].items, Items))
        self.assertEqual(getattr(prop['tags'].items, '$ref'), 'Tag')
        # status
        self.assertEqual(prop['status'].type, 'string')
        self.assertEqual(
            sorted(prop['status'].enum),
            sorted(['available', 'pending', 'sold']))

    def test_field_name(self):
        """ field_name """
        self.assertEqual(
            sorted(self.app.raw._field_names_),
            sorted([
                'info', 'authorizations', 'apiVersion', 'swaggerVersion', 'apis'
            ]))

    def test_children(self):
        """ children """
        children = self.app.raw._children_
        self.assertEqual(len(children), 5)
        self.assertEqual(
            set(['/user', '/pet', '/store']),
            set([
                child.path for child in six.itervalues(children)
                if isinstance(child, ResourceInListing)
            ]))
