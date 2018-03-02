from __future__ import absolute_import
from ....scan import Dispatcher
from ....errs import SchemaError
from ....utils import scope_compose, get_or_none
from .... import consts
from ..objects import (
    ResourceListing,
    ApiDeclaration,
    Operation,
    Authorization,
    Parameter,
    Model,
)
from ...v2_0.objects import Swagger
import os
import six


def _get_name(path):
    return path.split('/', 3)[2]


def update_type_and_ref(dst, src, scope, sep, app):
    ref = getattr(src, '$ref')
    if ref:
        dst['$ref'] = '#/definitions/' + scope_compose(scope, ref, sep=sep)

    if app.prim_factory.is_primitive(getattr(src, 'type', None)):
        dst['type'] = src.type.lower()
    elif src.type:
        dst['$ref'] = '#/definitions/' + scope_compose(scope, src.type, sep=sep)

def convert_min_max(dst, src):
    def _from_str(name):
        v = getattr(src, name, None)
        if v:
            if src.type == 'integer':
                # we need to handle 1.0 when converting to int
                # that's why we need to convert to float first
                dst[name] = int(float(v))
            elif src.type == 'number':
                dst[name] = float(v)
            else:
                raise SchemaError('minimum/maximum is only allowed on integer/number, not {0}'.format(src.type))
        else:
            dst.pop(name, None)

    _from_str('minimum')
    _from_str('maximum')


def convert_schema_from_datatype(obj, scope, sep, app):
    if obj == None:
        return None

    spec = {}
    update_type_and_ref(spec, obj, scope, sep, app)
    if obj.is_set('format'):
        spec['format'] = obj.format
    if obj.is_set('defaultValue'):
        spec['default'] = obj.defaultValue
    convert_min_max(spec, obj)
    spec['uniqueItems'] = obj.uniqueItems
    spec['enum'] = obj.enum
    if obj.items:
        item_spec = {}
        update_type_and_ref(item_spec, obj.items, scope, sep, app)
        item_spec['format'] = obj.items.format
        spec['items'] = item_spec

    return spec

def convert_items(o, app):
    items_spec = {}
    if getattr(o, '$ref'):
        raise SchemaError('Can\'t have $ref for Items')
    if not app.prim_factory.is_primitive(getattr(o, 'type', None)):
        raise SchemaError('Non primitive type is not allowed for Items')
    items_spec['type'] = o.type.lower()

    if o.is_set('format'):
        items_spec['format'] = o.format

    return items_spec

def convert_parameter(param, scope, sep, app):
    p_spec = {}
    if param.is_set('name'):
        p_spec['name'] = param.name
    if param.is_set('required'):
        p_spec['required'] = param.required
    if param.is_set('description'):
        p_spec['description'] = param.description

    if param.paramType == 'form':
        p_spec['in'] = 'formData'
    else:
        p_spec['in'] = param.paramType

    if 'body' == p_spec['in']:
        p_spec['schema'] = convert_schema_from_datatype(param, scope, sep, app)
    else:
        if getattr(param, '$ref'):
            raise SchemaError('Can\'t have $ref in non-body Parameters')

        if param.allowMultiple == True and param.items == None:
            p_spec['type'] = 'array'
            p_spec['collectionFormat'] = 'csv'
            if param.is_set('uniqueItems'):
                p_spec['uniqueItems'] = param.uniqueItems
            p_spec['items'] = convert_items(param, app)
            if param.is_set("defaultValue"):
                p_spec['default'] = [param.defaultValue]
            p_spec['items']['enum'] = param.enum
        else:
            p_spec['type'] = param.type.lower()
            if param.is_set('format'):
                p_spec['format'] = param.format
            if param.is_set("defaultValue"):
                p_spec['default'] = param.defaultValue
            convert_min_max(p_spec, param)
            p_spec['enum'] = param.enum

        if param.items:
            p_spec['collectionFormat'] = 'csv'
            if param.is_set('uniqueItems'):
                p_spec['uniqueItems'] = param.uniqueItems
            p_spec['items'] = convert_items(param.items, app)

    return p_spec

def convert_operation(op, api, api_decl, swagger, sep, app):
    op_spec = {}

    scope = api_decl.resourcePath[1:]
    if scope:
        op_spec['tags'] = [scope]
    if op.is_set('nickname'):
        op_spec['operationId'] = op.nickname
    if op.is_set('summary'):
        op_spec['summary'] = op.summary
    if op.is_set('notes'):
        op_spec['description'] = op.notes
    op_spec['deprecated'] = op.deprecated == 'true'

    c = op.consumes if op.consumes else api_decl.consumes
    if c:
        op_spec['consumes'] = c if c else []

    p = op.produces if op.produces else api_decl.produces
    if p:
        op_spec['produces'] = p if p else []

    parameters = op_spec.setdefault('parameters', [])
    for p in op.parameters:
        parameters.append(convert_parameter(p, scope, sep, app))

    # if there is not authorizations in this operation,
    # looking for it in api-declaration object.
    _auth = op.authorizations if op.authorizations else api_decl.authorizations
    if _auth:
        op_spec['security'] = []
        for name, scopes in six.iteritems(_auth):
            op_spec['security'].append({name: [v.scope for v in scopes]})

    # Operation return value
    op_spec['responses'] = {}
    resp_spec = {}
    if op.type != 'void':
        resp_spec['schema'] = convert_schema_from_datatype(op, scope, sep, app)
    resp_spec['description'] = '' # description is a required field in 2.0 Response object
    op_spec['responses']['default'] = resp_spec

    path = api_decl.base_path + api.path
    if path not in swagger['paths']:
        swagger['paths'][path] = {}

    method = op.method.lower()
    swagger['paths'][path][method] = op_spec

def convert_model(model, api_decl, swagger, sep, app):
    scope = api_decl.resourcePath[1:]

    # Ex. a 'Status' model under 'Pet' resource
    # => new model-id would be 'Pet##Status'
    s = scope_compose(scope, model.id, sep=sep)
    s_spec = swagger['definitions'].setdefault(s, {})

    props = {}
    for name, prop in six.iteritems(model.properties):
        props[name] = convert_schema_from_datatype(prop, scope, sep, app)
        props[name]['description'] = prop.description

    s_spec.setdefault('properties', {}).update(props)

    if model.is_set('required'):
        s_spec['required'] = model.required
    if model.is_set('discriminator'):
        s_spec['discriminator'] = model.discriminator
    if model.is_set('description'):
        s_spec['description'] = model.description

    for t in model.subTypes or []:
        # here we assume those child models belongs to
        # the same resource.
        sub_s = scope_compose(scope, t, sep=sep)
        sub_o_spec = swagger['definitions'].setdefault(sub_s, {})

        new_ref = {}
        new_ref['$ref'] = '#/definitions/' + s
        sub_o_spec.setdefault('allOf', []).append(new_ref)


class Upgrade(object):
    """ convert 1.2 object to 2.0 object
    """
    class Disp(Dispatcher): pass

    def __init__(self, app, sep=consts.SCOPE_SEPARATOR):
        self.app = app
        self.__swagger = None
        self.__sep = sep

    @Disp.register([ResourceListing])
    def _resource_listing(self, path, obj):
        swagger_spec = {}
        swagger_spec['swagger'] = '2.0'
        swagger_spec['schemes'] = ['http', 'https']
        swagger_spec['host'] = ''
        swagger_spec['basePath'] = ''
        swagger_spec['tags'] = []
        swagger_spec['definitions'] = {}
        swagger_spec['parameters'] = {}
        swagger_spec['responses'] = {}
        swagger_spec['paths'] = {}
        swagger_spec['security'] = []
        swagger_spec['securityDefinitions'] = {}
        swagger_spec['consumes'] = []
        swagger_spec['produces'] = []

        #   Info Object
        info_spec = {}
        info_spec['version'] = obj.apiVersion
        title = get_or_none(obj, 'info', 'title')
        if title:
            info_spec['title'] = title
        description = get_or_none(obj, 'info', 'description')
        if description:
            info_spec['description'] = description
        terms_of_service = get_or_none(obj, 'info', 'termsOfServiceUrl')
        if terms_of_service:
            info_spec['termsOfService'] = terms_of_service

        #       Contact Object
        if obj.info.contact:
            contact_spec = {}
            email = get_or_none(obj, 'info', 'contact')
            if email:
                contact_spec['email'] = email
            info_spec['contact'] = contact_spec
        #       License Object
        if obj.info.license or obj.info.licenseUrl:
            license_spec = {}
            name = get_or_none(obj, 'info', 'license')
            if name:
                license_spec['name'] = name
            url = get_or_none(obj, 'info', 'licenseUrl')
            if url:
                license_spec['url'] = url
            info_spec['license'] = license_spec

        swagger_spec['info'] = info_spec

        self.__swagger = swagger_spec

    @Disp.register([ApiDeclaration])
    def _api_declaration(self, path, obj):
        name = obj.resource_path[1:]
        for t in self.__swagger['tags']:
            if t['name'] == name:
                break
        else:
            tag_spec = {}
            tag_spec['name'] = name
            self.__swagger['tags'].append(tag_spec)

        for api in obj.apis:
            for op in api.operations:
                convert_operation(op, api, obj, self.__swagger, self.__sep, self.app)
        for _, model in obj.models.iteritems():
            convert_model(model, obj, self.__swagger, self.__sep, self.app)

    @Disp.register([Authorization])
    def _authorization(self, path, obj):
        ss_spec = {}
        if obj.type == 'basicAuth':
            ss_spec['type'] = 'basic'
        else:
            ss_spec['type'] = obj.type
        ss_spec['scopes'] = {}
        for s in obj.scopes or []:
            ss_spec['scopes'][s.scope] = s.description

        if ss_spec['type'] == 'oauth2':
            authorization_url = get_or_none(obj, 'grantTypes', 'implicit', 'loginEndpoint', 'url')
            if authorization_url:
                ss_spec['authorizationUrl'] = authorization_url
            token_url = get_or_none(obj, 'grantTypes', 'authorization_code', 'tokenEndpoint', 'url')
            if token_url:
                ss_spec['tokenUrl'] = token_url

            if authorization_url:
                ss_spec['flow'] = 'implicit'
            elif token_url:
                ss_spec['flow'] = 'access_code'
        elif ss_spec['type'] == 'apiKey':
            ss_spec['name'] = obj.keyname
            ss_spec['in'] = obj.passAs

        self.__swagger['securityDefinitions'][_get_name(path)] = ss_spec

    def get_swagger(self):
        """ some preparation before returning Swagger object
        """
        # prepare Swagger.host & Swagger.basePath
        if not self.__swagger:
            return None

        common_path = os.path.commonprefix(list(self.__swagger['paths'].keys()))
        # remove tailing slash,
        # because all paths in Paths Object would prefixed with slah.
        common_path = common_path[:-1] if common_path[-1] == '/' else common_path

        if len(common_path) > 0:
            p = six.moves.urllib.parse.urlparse(common_path)
            self.__swagger['host'] = p.netloc

            new_common_path = six.moves.urllib.parse.urlunparse((
                p.scheme, p.netloc, '', '', '', ''))
            new_path = {}
            for k in self.__swagger['paths'].keys():
                new_path[k[len(new_common_path):]] = self.__swagger['paths'][k]
            self.__swagger['paths'] = new_path

        return Swagger(self.__swagger, '#')

