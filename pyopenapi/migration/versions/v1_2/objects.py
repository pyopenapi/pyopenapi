# -*- coding: utf-8 -*-

from __future__ import absolute_import
from ...spec import Base2, rename, list_, map_


# pylint: disable=invalid-name
class BaseObj_v1_2(Base2):
    __swagger_version__ = '1.2'


class Items(BaseObj_v1_2):
    """ Items Object
    """
    __fields__ = {
        '$ref': dict(),
        'type': dict(),
        'format': dict(),
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
        'type': dict(),
        '$ref': dict(),
        'format': dict(),
        'defaultValue': dict(),
        'enum': dict(),
        'minimum': dict(),
        'maximum': dict(),
        'uniqueItems': dict(),
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
        'scope': dict(required=True),
        'description': dict(),
    }


class LoginEndpoint(BaseObj_v1_2):
    """ LoginEndpoint Object
    """

    __fields__ = {
        'url': dict(required=True),
    }


class Implicit(BaseObj_v1_2):
    """ Implicit Object
    """

    __fields__ = {
        'tokenName': dict(),
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
        'url': dict(required=True),
        'clientIdName': dict(),
        'clientSecretName': dict(),
    }

    __internal__ = {
        'client_id_name': dict(key='clientIdName', builder=rename),
        'client_secret_name': dict(key='clientSecretName', builder=rename),
    }


class TokenEndpoint(BaseObj_v1_2):
    """ TokenEndpoint Object
    """

    __fields__ = {
        'url': dict(required=True),
        'tokenName': dict(),
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
        'token_request_endpoint': dict(
            key='tokenRequestEndpoint', builder=rename),
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
        'scope': dict(),
        'description': dict(),
    }


class Authorization(BaseObj_v1_2):
    """ Authorization Object
    """

    __fields__ = {
        'type': dict(),
        'passAs': dict(),
        'keyname': dict(),
    }

    __children__ = {
        'scopes': dict(child_builder=list_(Scope)),
        'grantTypes': dict(child_builder=GrantTypes),
    }

    __internal__ = {
        'type_': dict(key='type', builder=rename),
        'pass_as': dict(key='passAs', builder=rename),
        'grant_types': dict(key='grantTypes', builder=rename),
    }


class ResponseMessage(BaseObj_v1_2):
    """ ResponseMessage Object
    """

    __fields__ = {
        'code': dict(required=True),
        'message': dict(required=True),
        'responseModel': dict(),
    }

    __internal__ = {
        'response_model': dict(key='responseModel', builder=rename),
    }


class Parameter(DataTypeObj):
    """ Parameter Object
    """

    __fields__ = {
        'paramType': dict(required=True),
        'name': dict(required=True),
        'description': dict(),
        'required': dict(),
        'allowMultiple': dict(),
    }

    __internal__ = {
        'param_type': dict(key='paramType', builder=rename),
        'allow_multiple': dict(key='allowMultiple', builder=rename),
    }


class Operation(DataTypeObj):
    """ Operation Object
    """

    __fields__ = {
        'method': dict(required=True),
        'summary': dict(),
        'notes': dict(),
        'nickname': dict(required=True),
        'produces': dict(),
        'consumes': dict(),
        'deprecated': dict(),
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
        'path': dict(required=True),
        'description': dict(),
    }

    __children__ = {
        'operations': dict(child_builder=list_(Operation)),
    }


class Property(DataTypeObj):
    """ Property Object
    """

    __fields__ = {
        'description': dict(),
    }


class Model(BaseObj_v1_2):
    """ Model Object
    """

    __fields__ = {
        'id': dict(required=True),
        'description': dict(),
        'required': dict(),
        'subTypes': dict(),
        'discriminator': dict(),
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
        'swaggerVersion': dict(required=True),
        'apiVersion': dict(),
        'basePath': dict(required=True),
        'resourcePath': dict(),
        'produces': dict(),
        'consumes': dict(),
        'description': dict(),
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
        'title': dict(required=True),
        'description': dict(required=True),
        'termsOfServiceUrl': dict(),
        'contact': dict(),
        'license': dict(),
        'licenseUrl': dict(),
    }

    __internal__ = {
        'terms_of_service_url': dict(key='termsOfServiceUrl', builder=rename),
        'license_url': dict(key='licenseUrl', builder=rename),
    }


class ResourceInListing(BaseObj_v1_2):
    """ Resource object in "Resource Listing"
    """
    __fields__ = {
        'path': dict(),
        'description': dict(),
    }


class ResourceListing(BaseObj_v1_2):
    """ Resource List Object
    """
    __fields__ = {
        'swaggerVersion': dict(required=True),
        'apiVersion': dict(),
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
