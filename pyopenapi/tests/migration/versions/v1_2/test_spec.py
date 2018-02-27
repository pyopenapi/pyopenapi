from pyopenapi.migration.versions.v1_2.objects import (
    Info,
    Authorization,
    Scope,
    Items,
    GrantTypes,
    Implicit,
    AuthorizationCode,
    LoginEndpoint,
    TokenRequestEndpoint,
    TokenEndpoint,
    ApiDeclaration,
    ResourceInListing,
    Operation,
    Parameter,
    ResponseMessage,
    Authorizations,
    Model)
from ....utils import get_test_data_folder, SampleApp
import unittest
import six


app = SampleApp.create(
    get_test_data_folder(version='1.2', which='wordnik'),
    to_spec_version='2.0'
)

class PropertyTestCase(unittest.TestCase):
    """ make sure properties' existence & type """

    def test_resource_list(self):
        """ resource list """
        self.assertTrue(isinstance(app.raw.info, Info))
        self.assertEqual(app.raw.info.title, 'Swagger Sample App')
        self.assertEqual(app.raw.swaggerVersion, '1.2')

    def test_authorizations(self):
        """ authorizations """
        self.assertTrue('oauth2' in app.raw.authorizations)
        self.assertTrue(isinstance(app.raw.authorizations['oauth2'], Authorization))
        self.assertEqual(app.raw.authorizations['oauth2'].type, 'oauth2')

    def test_scope(self):
        """ scope """
        auth = app.raw.authorizations['oauth2']
        self.assertEqual(len(auth.scopes), 2)
        self.assertTrue(isinstance(auth.scopes[0], Scope))
        self.assertTrue(isinstance(auth.scopes[0], Scope))
        self.assertEqual(auth.scopes[0].scope, 'write:pets')
        self.assertEqual(auth.scopes[1].scope, 'read:pets')
        self.assertEqual(auth.scopes[1].description, 'Read your pets')

    def test_grant_types(self):
        """ grant types """
        auth = app.raw.authorizations['oauth2']
        self.assertTrue(isinstance(auth.grantTypes, GrantTypes))

    def test_implicit(self):
        """ implicit """
        grant = app.raw.authorizations['oauth2'].grantTypes
        self.assertTrue(isinstance(grant.implicit, Implicit))
        self.assertEqual(grant.implicit.tokenName, 'access_token')

    def test_login_endpoint(self):
        """ login endpoint """
        implicit = app.raw.authorizations['oauth2'].grantTypes.implicit
        self.assertTrue(isinstance(implicit.loginEndpoint, LoginEndpoint))
        self.assertEqual(implicit.loginEndpoint.url,
            'http://petstore.swagger.wordnik.com/api/oauth/dialog')


    def test_authorization_code(self):
        """ authorization code """
        grant = app.raw.authorizations['oauth2'].grantTypes
        self.assertTrue(isinstance(grant.authorization_code, AuthorizationCode))

    def test_token_request_endpoint(self):
        """ token request endpoint """
        auth = app.raw.authorizations['oauth2'].grantTypes.authorization_code
        self.assertTrue(isinstance(auth.tokenRequestEndpoint,TokenRequestEndpoint))
        self.assertEqual(auth.tokenRequestEndpoint.url,
            'http://petstore.swagger.wordnik.com/api/oauth/requestToken')
        self.assertEqual(auth.tokenRequestEndpoint.clientIdName, 'client_id')
        self.assertEqual(auth.tokenRequestEndpoint.clientSecretName, 'client_secret')

    def test_token_endpoint(self):
        """ token endpoint """
        auth = app.raw.authorizations['oauth2'].grantTypes.authorization_code
        self.assertTrue(isinstance(auth.tokenEndpoint, TokenEndpoint))
        self.assertEqual(auth.tokenEndpoint.url,
            'http://petstore.swagger.wordnik.com/api/oauth/token')
        self.assertEqual(auth.tokenEndpoint.tokenName, 'auth_code')

    def test_resource_pet(self):
        """ resource """
        pet = app.raw.cached_apis['pet']
        self.assertTrue(isinstance(pet, ApiDeclaration))
        self.assertEqual(pet.swaggerVersion, '1.2')
        self.assertEqual(pet.apiVersion, '1.0.0')
        self.assertEqual(pet.basePath, 'http://petstore.swagger.wordnik.com/api')
        self.assertEqual(pet.resourcePath, '/pet')
        self.assertTrue('application/json' in pet.produces)
        self.assertTrue('application/xml' in pet.produces)
        self.assertTrue('text/plain' in pet.produces)
        self.assertTrue('text/html' in pet.produces)

    def test_operation(self):
        """ operation """
        pet = app.raw.cached_apis['pet']

        # find each operation's nickname
        nick_names = []
        for api in pet.apis:
            nick_names.extend([op.nickname for op in api.operations])

        self.assertEqual(sorted(nick_names), sorted([
            'updatePet',
            'addPet',
            'findPetsByStatus',
            'findPetsByTags',
            'partialUpdate',
            'updatePetWithForm',
            'deletePet',
            'getPetById',
            'uploadFile']
        ))

        updatePet = pet.apis[1].operations[1]
        # make sure we locate the right operation to test
        self.assertEqual(updatePet.nickname, 'updatePet')

        self.assertTrue(isinstance(updatePet, Operation))
        self.assertEqual(updatePet.method, 'PUT')
        self.assertEqual(updatePet.summary, 'Update an existing pet')
        self.assertEqual(updatePet.notes, '')

    def test_parameter(self):
        """ parameter """
        updatePet = app.raw.cached_apis['pet'].apis[1].operations[1]
        # make sure we locate the right operation to test
        self.assertEqual(updatePet.nickname, 'updatePet')

        p = updatePet.parameters[0]
        self.assertTrue(isinstance(p, Parameter))
        self.assertEqual(p.paramType, 'body')
        self.assertEqual(p.name, 'body')
        self.assertEqual(p.required, True)
        self.assertEqual(p.allowMultiple, False)
        self.assertEqual(p.description, 'Pet object that needs to be updated in the store')

    def test_response_message(self):
        """ response message """
        updatePet = app.raw.cached_apis['pet'].apis[1].operations[1]
        msg = updatePet.responseMessages[0]
        self.assertTrue(isinstance(msg, ResponseMessage))
        self.assertEqual(msg.code, 400)
        self.assertEqual(msg.message, 'Invalid ID supplied')

    def test_model(self):
        """ model """
        m = app.raw.cached_apis['pet'].models['Pet']
        self.assertTrue(isinstance(m, Model))
        self.assertEqual(m.id, 'Pet');
        self.assertEqual(sorted(m.required), sorted(['id', 'name']))

    def test_authorization(self):
        """ authorization """
        # make sure we locate the expected operation
        op = app.raw.cached_apis['pet'].apis[0].operations[2]
        self.assertEqual(op.nickname, 'partialUpdate')

        auth = op.authorizations['oauth2'][0]
        self.assertTrue(isinstance(auth, Authorizations))
        self.assertEqual(auth.scope, 'write:pets')

    def test_parent(self):
        """ make sure parent is assigned """
        self.assertTrue(app.raw.cached_apis['pet'].models['Pet']._parent_._parent_ is app.raw.cached_apis['pet'])

        getUserByName = app.raw.cached_apis['user'].apis[0].operations[2]
        self.assertEqual(getUserByName.nickname, 'getUserByName')
        self.assertTrue(getUserByName._parent_._parent_._parent_._parent_ is app.raw.cached_apis['user'])

        self.assertTrue(app.raw.info._parent_ is app.raw)


class DataTypeTestCase(unittest.TestCase):
    """ make sure data type ready """

    def test_operation(self):
        """ operation """
        op = app.raw.cached_apis['pet'].apis[2].operations[0]
        self.assertEqual(op.nickname, 'findPetsByStatus')
        self.assertEqual(op.type, 'array')
        self.assertEqual(getattr(op.items, '$ref'), 'Pet')

    def test_parameter(self):
        """ parameter """
        op = app.raw.cached_apis['pet'].apis[2].operations[0]
        self.assertEqual(op.nickname, 'findPetsByStatus')

        p = op.parameters[0]
        self.assertTrue(isinstance(p, Parameter))
        self.assertEqual(p.required, True)
        self.assertEqual(p.defaultValue, 'available')
        self.assertEqual(p.type, 'string')
        self.assertTrue(isinstance(p.enum, list))
        self.assertEqual(sorted(p.enum), sorted(['available', 'pending', 'sold']))

    def test_property(self):
        """ property """
        p = app.raw.cached_apis['pet'].models['Pet'].properties
        # id
        self.assertEqual(p['id'].type, 'integer')
        self.assertEqual(p['id'].format, 'int64')
        # we are not convert to real type here,
        # this case is handled by Upgrading from 1.2 to 2.0
        self.assertEqual(p['id'].minimum, '0.0')
        self.assertEqual(p['id'].maximum, '100.0')
        # category
        self.assertEqual(getattr(p['category'], '$ref'), 'Category')
        # name
        self.assertEqual(p['name'].type, 'string')
        # photoUrls
        self.assertEqual(p['photoUrls'].type, 'array')
        self.assertTrue(isinstance(p['photoUrls'].items, Items))
        self.assertEqual(p['photoUrls'].items.type, 'string')
        # tag
        self.assertEqual(p['tags'].type, 'array')
        self.assertTrue(isinstance(p['tags'].items, Items))
        self.assertEqual(getattr(p['tags'].items, '$ref'), 'Tag')
        # status
        self.assertEqual(p['status'].type, 'string')
        self.assertEqual(sorted(p['status'].enum), sorted(['available', 'pending', 'sold']))

    def test_field_name(self):
        """ field_name """
        self.assertEqual(sorted(app.raw._field_names_), sorted(['info', 'authorizations', 'apiVersion', 'swaggerVersion', 'apis']))

    def test_children(self):
        """ children """
        chd = app.raw._children_
        self.assertEqual(len(chd), 5)
        self.assertEqual(set(['/user', '/pet', '/store']), set([v.path for v in six.itervalues(chd) if isinstance(v, ResourceInListing)]))

