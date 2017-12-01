from __future__ import absolute_import
from ..base2 import Base2, field, child, list_, map_
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

    __renamed__ = {
        'ref': dict(key='$ref'),
        'type_': dict(key='type'),
        'format_': dict(key='format'),
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

    __renamed__ = {
        'type_': dict(key='type'),
        'ref': dict(key='$ref'),
        'format_': dict(key='format'),
        'default_value': dict(key='defaultValue'),
        'unique_items': dict(key='uniqueItems'),
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

    __renamed__ = {
        'token_name': dict(key='tokenName'),
        'login_endpoint': dict(key='loginEndpoint'),
    }


class TokenRequestEndpoint(BaseObj_v1_2):
    """ TokenRequestEndpoint Object
    """

    __fields__ = {
        'url': dict(builder=field, required=True),
        'clientIdName': dict(builder=field),
        'clientSecretName': dict(builder=field),
    }

    __renamed__ = {
        'client_id_name': dict(key='clientIdName'),
        'client_secret_name': dict(key='clientSecretName'),
    }


class TokenEndpoint(BaseObj_v1_2):
    """ TokenEndpoint Object
    """

    __fields__ = {
        'url': dict(builder=field, required=True),
        'tokenName': dict(builder=field),
    }

    __renamed__ = {
        'token_name': dict(key='tokenName'),
    }


class AuthorizationCode(BaseObj_v1_2):
    """ AuthorizationCode Object
    """

    __children__ = {
        'tokenRequestEndpoint': dict(child_builder=TokenRequestEndpoint),
        'tokenEndpoint': dict(child_builder=TokenEndpoint),
    }

    __renamed__ = {
        'token_request_endpoint': dict(key='tokenRequestEndpoint'),
        'token_endpoint': dict(key='tokenEndpoint'),
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

    __renamed__ = {
        'type_': dict(key='type'),
        'pass_as': dict(key='passAs'),
        'grantTypes': dict(key='grant_types'),
    }


class ResponseMessage(BaseObj_v1_2):
    """ ResponseMessage Object
    """

    __fields__ = {
        'code': dict(builder=field, required=True),
        'message': dict(builder=field, required=True),
        'responseModel': dict(builder=field),
    }

    __renamed__ = {
        'response_model': dict(key='responseModel'),
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

    __renamed__ = {
        'param_type': dict(key='paramType'),
        'allow_multiple': dict(key='allowMultiple'),
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

    __renamed__ = {
        'response_messages': dict(key='responseMessages')
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

    __renamed__ = {
        'id_': dict(key='id'),
        'sub_types': dict(key='subTypes'),
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

    __renamed__ = {
        'swagger_version': dict(key='swaggerVersion'),
        'api_version': dict(key='apiVersion'),
        'base_path': dict(key='basePath'),
        'resource_path': dict(key='resourcePath'),
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

    __renamed__ = {
        'terms_of_service_url': dict(key='termsOfServiceUrl'),
        'license_url': dict(key='licenseUrl'),
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

    __renamed__ = {
        'swagger_version': dict(key='swaggerVersion'),
        'api_version': dict(key='apiVersion'),
    }

    __internal__ = {
        'cached_apis': dict(),
    }
