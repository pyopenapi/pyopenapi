from __future__ import absolute_import
from ..base2 import Base2, field, child, rename, list_, map_
import six
import copy


class BaseObj_v1_2(Base2):
    __swagger_version__ = '1.2'


class Items(BaseObj_v1_2):
    """ Items Object
    """
    __fields__ = {
        '$ref': dict(builder=field),
        'type': dict(builder=field),
        'format': dict(builder=field),
    }

    __internal__ = {
        'ref': dict(key='$ref', builder=rename),
        'type_': dict(key='type', builder=rename),
        'format_': dict(key='format', builder=rename),
    }


class DataTypeObj(BaseObj_v1_2):
    """ Data Type Fields
    """
    __fields__ = {
        'type': dict(builder=field),
        '$ref': dict(builder=field),
        'format': dict(builder=field),
        'defaultValue': dict(builder=field),
        'enum': dict(builder=field),
        'minimum': dict(builder=field),
        'maximum': dict(builder=field),
        'uniqueItems': dict(builder=field),
    }

    __children__ = {
        'items': dict(child_builder=Items),
    }

    __internal__ = {
        'type_': dict(key='type', builder=rename),
        'ref': dict(key='$ref', builder=rename),
        'format_': dict(key='format', builder=rename),
        'default_value': dict(key='defaultValue', builder=rename),
        'unique_items': dict(key='uniqueItems', builder=rename),
    }


class Scope(BaseObj_v1_2):
    """ Scope Object
    """

    __fields__ = {
        'scope': dict(builder=field, required=True),
        'description': dict(builder=field),
    }


class LoginEndpoint(BaseObj_v1_2):
    """ LoginEndpoint Object
    """

    __fields__ = {
        'url': dict(builder=field, required=True),
    }


class Implicit(BaseObj_v1_2):
    """ Implicit Object
    """

    __fields__ = {
        'tokenName': dict(builder=field),
    }

    __children__ = {
        'loginEndpoint': dict(child_builder=LoginEndpoint, required=True),
    }

    __internal__ = {
        'token_name': dict(key='tokenName', builder=rename),
        'login_endpoint': dict(key='loginEndpoint', builder=rename),
    }


class TokenRequestEndpoint(BaseObj_v1_2):
    """ TokenRequestEndpoint Object
    """

    __fields__ = {
        'url': dict(builder=field, required=True),
        'clientIdName': dict(builder=field),
        'clientSecretName': dict(builder=field),
    }

    __internal__ = {
        'client_id_name': dict(key='clientIdName', builder=rename),
        'client_secret_name': dict(key='clientSecretName', builder=rename),
    }


class TokenEndpoint(BaseObj_v1_2):
    """ TokenEndpoint Object
    """

    __fields__ = {
        'url': dict(builder=field, required=True),
        'tokenName': dict(builder=field),
    }

    __internal__ = {
        'token_name': dict(key='tokenName', builder=rename),
    }


class AuthorizationCode(BaseObj_v1_2):
    """ AuthorizationCode Object
    """

    __children__ = {
        'tokenRequestEndpoint': dict(child_builder=TokenRequestEndpoint),
        'tokenEndpoint': dict(child_builder=TokenEndpoint),
    }

    __internal__ = {
        'token_request_endpoint': dict(key='tokenRequestEndpoint', builder=rename),
        'token_endpoint': dict(key='tokenEndpoint', builder=rename),
    }


class GrantTypes(BaseObj_v1_2):
    """ GrantTypes Object
    """

    __children__ = {
        'implicit': dict(child_builder=Implicit),
        'authorization_code': dict(child_builder=AuthorizationCode),
    }


class Authorizations(BaseObj_v1_2):
    """ Authorizations Object
    """

    __fields__ = {
        'scope': dict(builder=field),
        'description': dict(builder=field),
    }


class Authorization(BaseObj_v1_2):
    """ Authorization Object
    """

    __fields__ = {
        'type': dict(builder=field),
        'passAs': dict(builder=field),
        'keyname': dict(builder=field),
    }

    __children__ = {
        'scopes': dict(child_builder=list_(Scope)),
        'grantTypes': dict(child_builder=GrantTypes),
    }

    __internal__ = {
        'type_': dict(key='type', builder=rename),
        'pass_as': dict(key='passAs', builder=rename),
        'grantTypes': dict(key='grant_types', builder=rename),
    }


class ResponseMessage(BaseObj_v1_2):
    """ ResponseMessage Object
    """

    __fields__ = {
        'code': dict(builder=field, required=True),
        'message': dict(builder=field, required=True),
        'responseModel': dict(builder=field),
    }

    __internal__ = {
        'response_model': dict(key='responseModel', builder=rename),
    }


class Parameter(DataTypeObj):
    """ Parameter Object
    """

    __fields__ = {
        'paramType': dict(builder=field, required=True),
        'name': dict(builder=field, required=True),
        'description': dict(builder=field),
        'required': dict(builder=field),
        'allowMultiple': dict(builder=field),
    }

    __internal__ = {
        'param_type': dict(key='paramType', builder=rename),
        'allow_multiple': dict(key='allowMultiple', builder=rename),
    }


class Operation(DataTypeObj):
    """ Operation Object
    """

    __fields__ = {
        'method': dict(builder=field, required=True),
        'summary': dict(builder=field),
        'notes': dict(builder=field),
        'nickname': dict(builder=field, required=True),
        'produces': dict(builder=field),
        'consumes': dict(builder=field),
        'deprecated': dict(builder=field),
    }

    __children__ = {
        'authorizations': dict(child_builder=map_(list_(Authorizations))),
        'parameters': dict(child_builder=list_(Parameter)),
        'responseMessages': dict(child_builder=list_(ResponseMessage)),
    }

    __internal__ = {
        'response_messages': dict(key='responseMessages', builder=rename)
    }


class Api(BaseObj_v1_2):
    """ Api Object
    """

    __fields__ = {
        'path': dict(builder=field, required=True),
        'description': dict(builder=field),
    }

    __children__ = {
        'operations': dict(child_builder=list_(Operation)),
    }


class Property(DataTypeObj):
    """ Property Object
    """

    __fields__ = {
        'description': dict(builder=field),
    }


class Model(BaseObj_v1_2):
    """ Model Object
    """

    __fields__ = {
        'id': dict(builder=field, required=True),
        'description': dict(builder=field),
        'required': dict(builder=field),
        'subTypes': dict(builder=field),
        'discriminator': dict(builder=field),
    }

    __children__ = {
        'properties': dict(child_builder=map_(Property), required=True),
    }

    __internal__ = {
        'id_': dict(key='id', builder=rename),
        'sub_types': dict(key='subTypes', builder=rename),
    }


class ApiDeclaration(BaseObj_v1_2):
    """ Resource Object
    The root object of each resource file
    """

    __fields__ = {
        'swaggerVersion': dict(builder=field, required=True),
        'apiVersion': dict(builder=field),
        'basePath': dict(builder=field, required=True),
        'resourcePath': dict(builder=field),
        'produces': dict(builder=field),
        'consumes': dict(builder=field),
        'description': dict(builder=field),
    }

    __children__ = {
        'apis': dict(child_builder=list_(Api), required=True),
        'models': dict(child_builder=map_(Model)),
        'authorizations': dict(child_builder=map_(list_(Authorizations))),
    }

    __internal__ = {
        'swagger_version': dict(key='swaggerVersion', builder=rename),
        'api_version': dict(key='apiVersion', builder=rename),
        'base_path': dict(key='basePath', builder=rename),
        'resource_path': dict(key='resourcePath', builder=rename),
    }


class Info(BaseObj_v1_2):
    """ Info Object
    """

    __fields__ = {
        'title': dict(builder=field, required=True),
        'description': dict(builder=field, required=True),
        'termsOfServiceUrl': dict(builder=field),
        'contact': dict(builder=field),
        'license': dict(builder=field),
        'licenseUrl': dict(builder=field),
    }

    __internal__ = {
        'terms_of_service_url': dict(key='termsOfServiceUrl', builder=rename),
        'license_url': dict(key='licenseUrl', builder=rename),
    }


class ResourceInListing(BaseObj_v1_2):
    """ Resource object in "Resource Listing"
    """
    __fields__ = {
        'path': dict(builder=field),
        'description': dict(builder=field),
    }


class ResourceListing(BaseObj_v1_2):
    """ Resource List Object
    """
    __fields__ = {
        'swaggerVersion': dict(builder=field, required=True),
        'apiVersion': dict(builder=field),
    }

    __children__ = {
        'apis': dict(child_builder=list_(ResourceInListing)),
        'info': dict(child_builder=Info),
        'authorizations': dict(child_builder=map_(Authorization)),
    }

    __internal__ = {
        'cached_apis': dict(),
        'swagger_version': dict(key='swaggerVersion', builder=rename),
        'api_version': dict(key='apiVersion', builder=rename),
    }
