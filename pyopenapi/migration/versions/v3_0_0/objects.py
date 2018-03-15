# -*- coding: utf-8 -*-

from __future__ import absolute_import
import six

from ...spec import Base2, rename, child, list_, map_


# pylint: disable=invalid-name
class Base2_v3_0_0(Base2):
    __swagger_version__ = '3.0.0'


class Reference(Base2_v3_0_0):
    __fields__ = {
        '$ref': dict(required=True, readonly=False),
    }

    __internal__ = {'ref': dict(key='$ref', builder=rename)}


def if_not_ref_else(class_builder):
    def _f(spec, path, override):
        if '$ref' in spec:
            return Reference(spec, path=path, override=override)
        return class_builder(spec, path=path, override=override)

    _f.__name__ = 'if_not_ref_else_' + class_builder.__name__
    return _f


def if_not_bool_else(class_builder):
    def _f(spec, path, override):
        if isinstance(spec, bool):
            return spec
        return class_builder(spec, path=path, override=override)

    _f.__name__ = 'if_not_bool_else_' + class_builder.__name__
    return _f


def is_str(spec, path, override):
    if override:
        raise Exception('attemp to override "str" in {}'.format(path))
    if isinstance(spec, six.string_types):
        return spec
    raise Exception('should be a string, not {}, {}'.format(
        str(type(spec)), path))


def is_str_or_int(spec, path, override):
    if override:
        raise Exception('attemp to override "str" in {}'.format(path))
    if isinstance(spec, six.string_types + six.integer_types):
        return spec
    raise Exception('should be a string or int, not {} in {}'.format(
        str(type(spec)), path))


class Contact(Base2_v3_0_0):
    __fields__ = {
        'name': dict(),
        'url': dict(),
        'email': dict(),
    }


class License(Base2_v3_0_0):
    __fields__ = {
        'name': dict(required=True),
        'url': dict(),
    }


class Info(Base2_v3_0_0):
    __fields__ = {
        'title': dict(required=True),
        'description': dict(),
        'termsOfService': dict(),
        'version': dict(required=True),
    }

    __children__ = {
        'contact': dict(child_builder=Contact),
        'license': dict(child_builder=License),
    }

    __internal__ = {
        'terms_of_service': dict(key='termsOfService', builder=rename),
    }


class ServerVariable(Base2_v3_0_0):
    __fields__ = {
        'default': dict(required=True),
        'description': dict(),
    }

    __children__ = {
        'enum': dict(child_builder=list_(is_str)),
    }

    __internal__ = {'enum_': dict(key='enum', builder=rename)}


class Server(Base2_v3_0_0):
    __fields__ = {
        'url': dict(required=True),
        'description': dict(),
    }

    __children__ = {
        'variables': dict(child_builder=map_(ServerVariable)),
    }


class Example(Base2_v3_0_0):
    __fields__ = {
        'summary': dict(),
        'description': dict(),
        'value': dict(),
        'externalValue': dict(),
    }

    __internal__ = {
        'external_value': dict(key='externalValue', builder=rename),
    }


ExampleOrReference = if_not_ref_else(Example)


class XML_(Base2_v3_0_0):
    __fields__ = {
        'name': dict(),
        'namespace': dict(),
        'prefix': dict(),
        'attribute': dict(),
        'wrapped': dict(),
    }


class ExternalDocumentation(Base2_v3_0_0):
    __fields__ = {
        'description': dict(),
        'url': dict(required=True),
    }


class Discriminator(Base2_v3_0_0):
    __fields__ = {
        'propertyName': dict(key='propertyName', ),
    }

    __children__ = {
        'mapping': dict(child_builder=map_(is_str)),
    }

    __internal__ = {
        'property_name': dict(key='propertyName', builder=rename),
    }


class Schema(Base2_v3_0_0):
    __fields__ = {
        'title': dict(),
        'multipleOf': dict(),
        'maximum': dict(),
        'exclusiveMaximum': dict(),
        'minimum': dict(),
        'exclusiveMinimum': dict(),
        'maxLength': dict(),
        'minLength': dict(),
        'pattern': dict(),
        'maxItems': dict(),
        'minItems': dict(),
        'uniqueItems': dict(),
        'maxProperties': dict(),
        'minProperties': dict(),
        'required': dict(),
        'enum': dict(),
        'type': dict(),
        'description': dict(),
        'format': dict(),
        'default': dict(),
        'nullable': dict(),
        'readOnly': dict(),
        'writeOnly': dict(),
        'example': dict(),
        'depreated': dict(),
    }

    __children__ = {
        'discriminator': dict(child_builder=Discriminator),
        'xml': dict(child_builder=XML_),
        'externalDocs': dict(child_builder=ExternalDocumentation),
    }

    __internal__ = {
        'multiple_of': dict(key='multipleOf', builder=rename),
        'exclusive_maximum': dict(key='exclusiveMaximum', builder=rename),
        'exclusive_minimum': dict(key='exclusiveMinimum', builder=rename),
        'max_length': dict(key='maxLength', builder=rename),
        'min_length': dict(key='minLength', builder=rename),
        'max_items': dict(key='maxItems', builder=rename),
        'min_items': dict(key='minItems', builder=rename),
        'unique_items': dict(key='uniqueItems', builder=rename),
        'max_properties': dict(key='maxProperties', builder=rename),
        'min_properties': dict(key='minProperties', builder=rename),
        'enum_': dict(key='enum', builder=rename),
        'type_': dict(key='type', builder=rename),
        'format_': dict(key='format', builder=rename),
        'read_only': dict(key='readOnly', builder=rename),
        'write_only': dict(key='writeOnly', builder=rename),
        'xml_': dict(key='xml', builder=rename),
        'external_docs': dict(key='externalDocs', builder=rename),
        'all_of': dict(key='allOf', builder=rename),
        'one_of': dict(key='oneOf', builder=rename),
        'any_of': dict(key='anyOf', builder=rename),
        'not_': dict(key='not', builder=rename),
        'additional_properties': dict(
            key='additionalProperties', builder=rename),
    }


SchemaOrReference = if_not_ref_else(Schema)
BoolOrSchemaOrReference = if_not_bool_else(SchemaOrReference)

Schema.attach_field(
    'allOf', builder=child, child_builder=list_(SchemaOrReference))
Schema.attach_field(
    'oneOf', builder=child, child_builder=list_(SchemaOrReference))
Schema.attach_field(
    'anyOf', builder=child, child_builder=list_(SchemaOrReference))
Schema.attach_field('not', builder=child, child_builder=SchemaOrReference)
Schema.attach_field('items', builder=child, child_builder=SchemaOrReference)
Schema.attach_field(
    'properties', builder=child, child_builder=map_(SchemaOrReference))
Schema.attach_field(
    'additionalProperties',
    builder=child,
    child_builder=BoolOrSchemaOrReference,
)


class Parameter(Base2_v3_0_0):
    __fields__ = {
        'name': dict(required=True),
        'in': dict(required=True),
        'description': dict(),
        'required': dict(),
        'deprecated': dict(),
        'allowEmptyValue': dict(),
        'style': dict(),
        'explode': dict(),
        'allowReserved': dict(),
        'example': dict(),
    }

    __children__ = {
        'examples': dict(child_builder=map_(ExampleOrReference)),
        'schema': dict(child_builder=SchemaOrReference),
    }

    __internal__ = {
        'in_': dict(key='in', builder=rename),
        'allow_empty_value': dict(key='allowEmptyValue', builder=rename),
        'allow_reserved': dict(key='allowReserved', builder=rename),
    }


ParameterOrReference = if_not_ref_else(Parameter)


class Header(Parameter):
    __fields__ = {
        'name': dict(restricted=True),
        'in': dict(restricted=True, default='header')
    }

    __internal__ = {
        'in_': dict(key='in', builder=rename),
    }


HeaderOrReference = if_not_ref_else(Header)


class Encoding(Base2_v3_0_0):
    __fields__ = {
        'contentType': dict(),
        'stype': dict(),
        'explode': dict(),
        'allowReserved': dict(),
    }

    __children__ = {
        'headers': dict(child_builder=map_(HeaderOrReference)),
    }

    __internal__ = {
        'content_type': dict(key='contentType', builder=rename),
        'allow_reserved': dict(key='allowReserved', builder=rename),
    }


class MediaType(Base2_v3_0_0):
    __fields__ = {
        'example': dict(),
    }

    __children__ = {
        'schema': dict(child_builder=SchemaOrReference),
        'examples': dict(child_builder=ExampleOrReference),
        'encoding': dict(child_builder=map_(Encoding)),
    }


Parameter.attach_field('content', builder=child, child_builder=map_(MediaType))


class RequestBody(Base2_v3_0_0):
    __fields__ = {
        'description': dict(),
        'required': dict(),
    }

    __children__ = {
        'content': dict(child_builder=map_(MediaType), required=True),
    }


RequestBodyOrReference = if_not_ref_else(RequestBody)


class Link(Base2_v3_0_0):
    __fields__ = {
        'operationRef': dict(),
        'operationId': dict(),
        'requestBody': dict(),
        'description': dict(),
    }

    __children__ = {
        'server': dict(child_builder=Server),
        'parameters': dict(child_builder=map_(is_str)),
    }

    __internal__ = {
        'operation_ref': dict(key='operationRef', builder=rename),
        'operation_id': dict(key='operationId', builder=rename),
        'request_body': dict(key='requestBody', builder=rename),
    }


LinkOrReference = if_not_ref_else(Link)


class Response(Base2_v3_0_0):
    __fields__ = {
        'description': dict(required=True),
    }

    __children__ = {
        'headers': dict(child_builder=map_(HeaderOrReference)),
        'content': dict(child_builder=map_(MediaType)),
        'links': dict(child_builder=map_(LinkOrReference)),
    }


ResponseOrReference = if_not_ref_else(Response)


class OAuthFlow(Base2_v3_0_0):
    __fields__ = {
        'authorizationUrl': dict(),
        'tokenUrl': dict(),
        'refreshUrl': dict(),
    }

    __children__ = {
        'scopes': dict(child_builder=map_(is_str), required=True),
    }

    __internal__ = {
        'authorization_url': dict(key='authorizationUrl', builder=rename),
        'token_url': dict(key='tokenUrl', builder=rename),
        'refresh_url': dict(key='refreshUrl', builder=rename),
    }


class OAuthFlows(Base2_v3_0_0):
    __children__ = {
        'implicit': dict(child_builder=OAuthFlow),
        'password': dict(child_builder=OAuthFlow),
        'clientCredentials': dict(child_builder=OAuthFlow),
        'authorizationCode': dict(child_builder=OAuthFlow),
    }

    __internal__ = {
        'client_credentials': dict(key='clientCredential', builder=rename),
        'authorization_code': dict(key='authorizationCode', builder=rename),
    }


class SecurityScheme(Base2_v3_0_0):
    __fields__ = {
        'type': dict(required=True),
        'description': dict(),
        'name': dict(),
        'in': dict(),
        'scheme': dict(),
        'bearerFormat': dict(),
        'openIdConnectUrl': dict(),
    }

    __children__ = {
        'flows': dict(child_builder=OAuthFlows),
    }

    __internal__ = {
        'type_': dict(key='type', builder=rename),
        'in_': dict(key='in', builder=rename),
        'bearer_format': dict(key='bearerFormat', builder=rename),
        'openid_connect_url': dict(key='openIdConnectUrl', builder=rename),
    }


SecuritySchemeOrReference = if_not_ref_else(SecurityScheme)


class Operation(Base2_v3_0_0):
    __fields__ = {
        'summary': dict(),
        'description': dict(),
        'operationId': dict(),
        'deprecated': dict(),
    }

    __children__ = {
        'externalDocs': dict(child_builder=ExternalDocumentation),
        'tags': dict(child_builder=list_(is_str)),
        'parameters': dict(child_builder=list_(ParameterOrReference)),
        'requestBody': dict(child_builder=RequestBodyOrReference),
        'responses': dict(child_builder=map_(ResponseOrReference)),
        'security': dict(child_builder=list_(map_(list_(is_str)))),
        'servers': dict(child_builder=list_(Server)),
    }

    __internal__ = {
        'external_docs': dict(key='externalDocs', builder=rename),
        'operation_id': dict(key='operationId', builder=rename),
        'request_body': dict(key='requestBody', builder=rename),
    }


class PathItem(Base2_v3_0_0):
    __fields__ = {
        '$ref': dict(readonly=False),
        'summary': dict(),
        'description': dict(),
    }

    __internal__ = {
        'ref':
        dict(key='$ref', builder=rename),
        'x_pyopenapi_internal_request_body':
        dict(key='x-pyopenapi_internal_request_body', builder=rename),
    }

    __children__ = {
        'get': dict(child_builder=Operation),
        'put': dict(child_builder=Operation),
        'post': dict(child_builder=Operation),
        'delete': dict(child_builder=Operation),
        'options': dict(child_builder=Operation),
        'head': dict(child_builder=Operation),
        'patch': dict(child_builder=Operation),
        'trace': dict(child_builder=Operation),
        'servers': dict(child_builder=list_(Server)),
        'parameters': dict(child_builder=list_(ParameterOrReference)),

        # a cached place for body parameter under PathItem object
        # in Swager 2.0 when migration
        'x-pyopenapi_internal_request_body': dict(child_builder=RequestBody),
    }


class Callback(map_(PathItem)):
    __swagger_version__ = '3.0.0'


CallbackOrReference = if_not_ref_else(Callback)
Operation.attach_field(
    'callbacks', builder=child, child_builder=map_(CallbackOrReference))


class Components(Base2_v3_0_0):
    __children__ = {
        'schemas': dict(child_builder=map_(SchemaOrReference)),
        'responses': dict(child_builder=map_(ResponseOrReference)),
        'parameters': dict(child_builder=map_(ParameterOrReference)),
        'examples': dict(child_builder=map_(ExampleOrReference)),
        'requestBodies': dict(child_builder=map_(RequestBodyOrReference)),
        'headers': dict(child_builder=map_(HeaderOrReference)),
        'securitySchemes': dict(child_builder=map_(SecuritySchemeOrReference)),
        'links': dict(child_builder=map_(LinkOrReference)),
        'callbacks': dict(child_builder=map_(CallbackOrReference)),
    }

    __internal__ = {
        'request_bodies': dict(key='requestBodies', builder=rename),
        'security_schemes': dict(key='securitySchemes', builder=rename),
    }


class Tag(Base2_v3_0_0):
    __fields__ = {
        'name': dict(required=True),
        'description': dict(),
    }

    __children__ = {
        'externalDocs': dict(child_builder=ExternalDocumentation),
    }

    __internal__ = {
        'external_docs': dict(key='externalDocs', builder=rename),
    }


class OpenApi(Base2_v3_0_0):
    __fields__ = {
        'openapi': dict(),
    }

    __children__ = {
        'info': dict(child_builder=Info),
        'servers': dict(child_builder=list_(Server)),
        'paths': dict(child_builder=map_(PathItem)),
        'components': dict(child_builder=Components),
        'security': dict(child_builder=list_(map_(list_(is_str)))),
        'tags': dict(child_builder=list_(Tag)),
        'externalDocs': dict(child_builder=ExternalDocumentation),
    }

    __internal__ = {
        'external_docs': dict(key='externalDocs', builder=rename),
    }
