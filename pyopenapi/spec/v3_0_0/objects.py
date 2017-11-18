from __future__ import absolute_import
from ..base2 import Base2, field, rename, child, internal, list_, map_
import six


class Base2_v3_0_0(Base2):
    __swagger_version__ = '3.0.0'


class Reference(Base2_v3_0_0):
    __fields__ = {
        'ref': dict(key='$ref', builder=field, required=True),

        # internal fields
        'normalized_ref': dict(builder=internal),
        'ref_obj': dict(builder=internal),
    }


def if_not_ref_else(class_builder):
    def _f(spec, path):
        if '$ref' in spec:
            return Reference(spec, path=path)
        return class_builder(spec, path=path)
    _f.__name__ = 'if_not_ref_else_' + class_builder.__name__
    return _f

def if_not_bool_else(class_builder):
    def _f(spec, path):
        if isinstance(spec, bool):
            return spec
        return class_builder(spec, path=path)
    _f.__name__ = 'if_not_bool_else_' + class_builder.__name__
    return _f

def is_str(spec, path):
    if isinstance(spec, six.string_types):
        return spec
    raise Exception('should be a string, not {}, {}'.format(str(type(spec)), path))

def is_str_or_int(spec, path):
    if isinstance(spec, six.string_types + six.integer_types):
        return spec
    raise Exception('should be a string or int, not {}'.format(str(type(spec)), path))


class Contact(Base2_v3_0_0):
    __fields__ = {
        'name': dict(builder=field),
        'url': dict(builder=field),
        'email': dict(builder=field),
    }


class License(Base2_v3_0_0):
    __fields__ = {
        'name': dict(builder=field, required=True),
        'url': dict(builder=field),
    }


class Info(Base2_v3_0_0):
    __fields__ = {
        'title': dict(builder=field, required=True),
        'description': dict(builder=field),
        'termsOfService': dict(builder=field),
        'contact': dict(builder=child, child_builder=Contact),
        'license': dict(builder=child, child_builder=License),
        'version': dict(builder=field, required=True),
    }

    __renamed__ = {
        'terms_of_service': dict(key='termsOfService'),
    }


class ServerVariable(Base2_v3_0_0):
    __fields__ = {
        'enum_': dict(key='enum', builder=child, child_builder=list_(is_str)),
        'default': dict(builder=field, required=True),
        'description': dict(builder=field),
    }


class Server(Base2_v3_0_0):
    __fields__ = {
        'url': dict(builder=field, required=True),
        'description': dict(builder=field),
        'variables': dict(builder=child, child_builder=map_(ServerVariable)),
    }


class Example(Base2_v3_0_0):
    __fields__ = {
        'summary': dict(builder=field),
        'description': dict(builder=field),
        'value': dict(builder=field),
        'externalValue': dict(builder=field),
    }

    __renamed__ = {
        'external_value': dict(key='externalValue'),
    }

ExampleOrReference = if_not_ref_else(Example)


class XML_(Base2_v3_0_0):
    __fields__ = {
        'name': dict(builder=field),
        'namespace': dict(builder=field),
        'prefix': dict(builder=field),
        'attribute': dict(builder=field),
        'wrapped': dict(builder=field),
    }


class ExternalDocumentation(Base2_v3_0_0):
    __fields__ = {
        'description': dict(builder=field),
        'url': dict(builder=field, required=True),
    }


class Discriminator(Base2_v3_0_0):
    __fields__ = {
        'propertyName': dict(key='propertyName', builder=field),
        'mapping': dict(builder=child, child_builder=map_(is_str)),
    }

    __renamed__ = {
        'property_name': dict(key='propertyName'),
    }


class Schema(Base2_v3_0_0):
    __fields__ = {
        'title': dict(builder=field),
        'multipleOf': dict(builder=field),
        'maximum': dict(builder=field),
        'exclusiveMaximum': dict(builder=field),
        'minimum': dict(builder=field),
        'exclusiveMinimum': dict(builder=field),
        'maxLength': dict(builder=field),
        'minLength': dict(builder=field),
        'pattern': dict(builder=field),
        'maxItems': dict(builder=field),
        'minItems': dict(builder=field),
        'uniqueItems': dict(builder=field),
        'maxProperties': dict(builder=field),
        'minProperties': dict(builder=field),
        'required': dict(builder=field),
        'enum': dict(builder=field),
        'type': dict(builder=field),
        'description': dict(builder=field),
        'format': dict(builder=field),
        'default': dict(builder=field),
        'nullable': dict(builder=field),
        'discriminator': dict(builder=child, child_builder=Discriminator),
        'readOnly': dict(builder=field),
        'writeOnly': dict(builder=field),
        'xml': dict(builder=child, child_builder=XML_),
        'externalDocs':  dict(builder=child, child_builder=ExternalDocumentation),
        'example': dict(builder=field),
        'depreated': dict(builder=field),
    }

    __renamed__ = {
        'multiple_of': dict(key='multipleOf'),
        'exclusive_maximum': dict(key='exclusiveMaximum'),
        'exclusive_minimum': dict(key='exclusiveMinimum'),
        'max_length': dict(key='maxLength'),
        'min_length': dict(key='minLength'),
        'max_items': dict(key='maxItems'),
        'min_items': dict(key='minItems'),
        'unique_items': dict(key='uniqueItems'),
        'max_properties': dict(key='maxProperties'),
        'min_properties': dict(key='minProperties'),
        'enum_': dict(key='enum'),
        'type_': dict(key='type'),
        'format_': dict(key='format'),
        'read_only': dict(key='readOnly'),
        'write_only': dict(key='writeOnly'),
        'xml_': dict(key='xml'),
        'external_docs': dict(key='externalDocs'),

        'all_of': dict(key='allOf'),
        'one_of': dict(key='oneOf'),
        'any_of': dict(key='anyOf'),
        'not_': dict(key='not'),
        'additional_properties': dict(key='additionalProperties'),
    }

SchemaOrReference = if_not_ref_else(Schema)
BoolOrSchemaOrReference = if_not_bool_else(SchemaOrReference)

Schema.attach_field('allOf', builder=child, child_builder=list_(SchemaOrReference))
Schema.attach_field('oneOf', builder=child, child_builder=list_(SchemaOrReference))
Schema.attach_field('anyOf', builder=child, child_builder=list_(SchemaOrReference))
Schema.attach_field('not', builder=child, child_builder=SchemaOrReference)
Schema.attach_field('items', builder=child, child_builder=SchemaOrReference)
Schema.attach_field('properties', builder=child, child_builder=map_(SchemaOrReference))
Schema.attach_field(
    'additionalProperties',
    builder=child,
    child_builder=BoolOrSchemaOrReference,
)


class Parameter(Base2_v3_0_0):
    __fields__ = {
        'name': dict(builder=field, required=True),
        'in': dict(builder=field, required=True),
        'description': dict(builder=field),
        'required': dict(builder=field),
        'deprecated': dict(builder=field),
        'allowEmptyValue': dict(builder=field),
        'style': dict(builder=field),
        'explode': dict(builder=field),
        'allowReserved': dict(builder=field),
        'schema': dict(builder=child, child_builder=SchemaOrReference),
        'example': dict(builder=field),
        'examples': dict(builder=child, child_builder=map_(ExampleOrReference)),
    }

    __renamed__ = {
        'in_': dict(key='in'),
        'allow_empty_value': dict(key='allowEmptyValue'),
        'allow_reserved': dict(key='allowReserved'),
    }

ParameterOrReference = if_not_ref_else(Parameter)


class Header(Parameter):
    __fields__ = {
        'name': dict(builder=field, restricted=True),
        'in': dict(builder=field, restricted=True, default='header')
    }

    __renamed__ = {
        'in_': dict(key='in'),
    }

HeaderOrReference = if_not_ref_else(Header)


class Encoding(Base2_v3_0_0):
    __fields__ = {
        'contentType': dict(builder=field),
        'headers': dict(builder=child, child_builder=map_(HeaderOrReference)),
        'stype': dict(builder=field),
        'explode': dict(builder=field),
        'allowReserved': dict(builder=field),
    }

    __renamed__ = {
        'content_type': dict(key='contentType'),
        'allow_reserved': dict(key='allowReserved'),
    }


class MediaType(Base2_v3_0_0):
    __fields__ = {
        'schema': dict(builder=child, child_builder=SchemaOrReference),
        'example': dict(builder=field),
        'examples': dict(builder=child, child_builder=ExampleOrReference),
        'encoding': dict(builder=child, child_builder=map_(Encoding)),
    }


Parameter.attach_field('content', builder=child, child_builder=map_(MediaType))


class RequestBody(Base2_v3_0_0):
    __fields__ = {
        'description': dict(builder=field),
        'content': dict(builder=child, child_builder=map_(MediaType), required=True),
        'required': dict(builder=field),
    }

RequestBodyOrReference = if_not_ref_else(RequestBody)


class Link(Base2_v3_0_0):
    __fields__ = {
        'operationRef': dict(builder=field),
        'operationId': dict(builder=field),
        'parameters': dict(builder=child, child_builder=map_(is_str)),
        'requestBody': dict(builder=field),
        'description': dict(builder=field),
        'server': dict(builder=child, child_builder=Server),
    }

    __renamed__ = {
        'operation_ref': dict(key='operationRef'),
        'operation_id': dict(key='operationId'),
        'request_body': dict(key='requestBody'),
    }

LinkOrReference = if_not_ref_else(Link)


class Response(Base2_v3_0_0):
    __fields__ = {
        'description': dict(builder=field, required=True),
        'headers': dict(builder=child, child_builder=map_(HeaderOrReference)),
        'content': dict(builder=child, child_builder=map_(MediaType)),
        'links': dict(builder=child, child_builder=map_(LinkOrReference)),
    }

ResponseOrReference = if_not_ref_else(Response)


class OAuthFlow(Base2_v3_0_0):
    __fields__ = {
        'authorizationUrl': dict(builder=field),
        'tokenUrl': dict(builder=field),
        'refreshUrl': dict(builder=field),
        'scopes': dict(builder=child, child_builder=map_(is_str), required=True),
    }

    __renamed__ = {
        'authorization_url': dict(key='authorizationUrl'),
        'token_url': dict(key='tokenUrl'),
        'refresh_url': dict(key='refreshUrl'),
    }


class OAuthFlows(Base2_v3_0_0):
    __fields__ = {
        'implicit': dict(builder=child, child_builder=OAuthFlow),
        'password': dict(builder=child, child_builder=OAuthFlow),
        'clientCredentials': dict(builder=child, child_builder=OAuthFlow),
        'authorizationCode': dict(builder=child, child_builder=OAuthFlow),
    }

    __renamed__ = {
        'client_credentials': dict(key='clientCredential'),
        'authorization_code': dict(key='authorizationCode'),
    }


class SecurityScheme(Base2_v3_0_0):
    __fields__ = {
        'type': dict(builder=field, required=True),
        'description': dict(builder=field),
        'name': dict(builder=field),
        'in': dict(builder=field),
        'scheme': dict(builder=field),
        'bearerFormat': dict(builder=field),
        'flows': dict(builder=child, child_builder=OAuthFlows),
        'openIdConnectUrl': dict(builder=field),
    }

    __renamed__ = {
        'type_': dict(key='type'),
        'in_': dict(key='in'),
        'bearer_format': dict(key='bearerFormat'),
        'openid_connect_url': dict(key='openIdConnectUrl'),
    }

SecuritySchemeOrReference = if_not_ref_else(SecurityScheme)


class Operation(Base2_v3_0_0):
    __fields__ = {
        'tags': dict(builder=child, child_builder=list_(is_str)),
        'summary': dict(builder=field),
        'description': dict(builder=field),
        'externalDocs': dict(builder=child, child_builder=ExternalDocumentation),
        'operationId': dict(builder=field),
        'parameters': dict(builder=child, child_builder=list_(ParameterOrReference)),
        'requestBody': dict(builder=child, child_builder=RequestBodyOrReference),
        'responses': dict(builder=child, child_builder=map_(ResponseOrReference)),
        'deprecated': dict(builder=field),
        'security': dict(builder=child, child_builder=list_(map_(list_(is_str)))),
        'servers': dict(builder=child, child_builder=list_(Server)),
    }

    __renamed__ = {
        'external_docs': dict(key='externalDocs'),
        'operation_id': dict(key='operationId'),
        'request_body': dict(key='requestBody'),
    }


class PathItem(Base2_v3_0_0):
    __fields__ = {
        '$ref': dict(builder=field),
        'summary': dict(builder=field),
        'description': dict(builder=field),
        'get': dict(builder=child, child_builder=Operation),
        'put': dict(builder=child, child_builder=Operation),
        'post': dict(builder=child, child_builder=Operation),
        'delete': dict(builder=child, child_builder=Operation),
        'options': dict(builder=child, child_builder=Operation),
        'head': dict(builder=child, child_builder=Operation),
        'patch': dict(builder=child, child_builder=Operation),
        'trace': dict(builder=child, child_builder=Operation),
        'servers': dict(builder=child, child_builder=list_(Server)),
        'parameters': dict(builder=child, child_builder=list_(ParameterOrReference)),

        # internal fields
        'normalized_ref': dict(builder=internal),
        'ref_obj': dict(builder=internal),
        'final_obj': dict(builder=internal),
    }

    __renamed__ = {
        'ref': dict(key='$ref'),
    }


class Callback(map_(PathItem)):
    __swagger_version__ = '3.0.0'


CallbackOrReference = if_not_ref_else(Callback)
Operation.attach_field('callbacks', builder=child, child_builder=map_(CallbackOrReference))


class Components(Base2_v3_0_0):
    __fields__ = {
        'schemas': dict(builder=child, child_builder=map_(SchemaOrReference)),
        'responses': dict(builder=child, child_builder=map_(ResponseOrReference)),
        'parameters': dict(builder=child, child_builder=map_(ParameterOrReference)),
        'examples': dict(builder=child, child_builder=map_(ExampleOrReference)),
        'requestBodies': dict(builder=child, child_builder=map_(RequestBodyOrReference)),
        'headers': dict(builder=child, child_builder=map_(HeaderOrReference)),
        'securitySchemes': dict(builder=child, child_builder=map_(SecuritySchemeOrReference)),
        'links': dict(builder=child, child_builder=map_(LinkOrReference)),
        'callbacks': dict(builder=child, child_builder=map_(CallbackOrReference)),
    }

    __renamed__ = {
        'request_bodies': dict(key='requestBodies'),
        'security_schemes': dict(key='securitySchemes'),
    }


class Tag(Base2_v3_0_0):
    __fields__ = {
        'name': dict(builder=field, required=True),
        'description': dict(builder=field),
        'externalDocs': dict(builder=child, child_builder=ExternalDocumentation),
    }

    __renamed__ = {
        'external_docs': dict(key='externalDocs'),
    }


class OpenApi(Base2_v3_0_0):
    __fields__ = {
        'openapi': dict(builder=field),
        'info': dict(builder=child, child_builder=Info),
        'servers': dict(builder=child, child_builder=list_(Server)),
        'paths': dict(builder=child, child_builder=map_(PathItem)),
        'components': dict(builder=child, child_builder=Components),
        'security': dict(builder=child, child_builder=list_(map_(list_(is_str)))),
        'tags': dict(builder=child, child_builder=list_(Tag)),
        'externalDocs': dict(builder=child, child_builder=ExternalDocumentation),
    }

    __renamed__ = {
        'external_docs': dict(key='externalDocs'),
    }

