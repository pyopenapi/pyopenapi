from __future__ import absolute_import
from ..base2 import Base2, field, child, internal, list_, map_
import six


class Base2_v3_0_0(Base2):
    __swagger_version__ = '3.0.0'


class Reference(Base2_v3_0_0):
    __fields__ = {
        'ref': dict(key='$ref', builder=field, required=True),
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
        'external_value': dict(key='externalValue', builder=field),
    }


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
        'property_name': dict(key='propertyName', builder=field),
        'mapping': dict(builder=child, child_builder=map_(is_str)),
    }


class Schema(Base2_v3_0_0):
    __fields__ = {
        'title': dict(builder=field),
        'multiple_of': dict(key='multipleOf', builder=field),
        'maximum': dict(builder=field),
        'exclusive_maximum': dict(key='exclusiveMaximum', builder=field),
        'minimum': dict(builder=field),
        'exclusive_minimum': dict(key='exclusiveMinimum', builder=field),
        'max_length': dict(key='maxLength', builder=field),
        'min_length': dict(key='minLength', builder=field),
        'pattern': dict(builder=field),
        'max_items': dict(key='maxItems', builder=field),
        'min_items': dict(key='minItems', builder=field),
        'unique_items': dict(key='uniqueItems', builder=field),
        'max_properties': dict(key='maxProperties', builder=field),
        'min_properties': dict(key='minProperties', builder=field),
        'required': dict(builder=field),
        'enum_': dict(key='enum', builder=field),
        'type_': dict(key='type', builder=field),
        'description': dict(builder=field),
        'format_': dict(key='format', builder=field),
        'default': dict(builder=field),
        'nullable': dict(builder=field),
        'discriminator': dict(builder=child, child_builder=Discriminator),
        'read_only': dict(key='readOnly', builder=field),
        'write_only': dict(key='writeOnly', builder=field),
        'xml_': dict(key='xml', builder=child, child_builder=XML_),
        'external_docs':  dict(key='externalDocs', builder=child, child_builder=ExternalDocumentation),
        'example': dict(builder=field),
        'depreated': dict(builder=field),
    }
Schema.attach_field('all_of', key='allOf', builder=child, child_builder=list_(if_not_ref_else(Schema)))
Schema.attach_field('one_of', key='oneOf',  builder=child, child_builder=list_(if_not_ref_else(Schema)))
Schema.attach_field('any_of', key='anyOf',  builder=child, child_builder=list_(if_not_ref_else(Schema)))
Schema.attach_field('not_', key='not',  builder=child, child_builder=if_not_ref_else(Schema))
Schema.attach_field('items', builder=child, child_builder=if_not_ref_else(Schema))
Schema.attach_field('properties', builder=child, child_builder=map_(if_not_ref_else(Schema)))
Schema.attach_field(
    'additional_properties',
    key='AdditionalProperties',
    builder=child,
    child_builder=if_not_bool_else(if_not_ref_else(Schema)),
)


class Parameter(Base2_v3_0_0):
    __fields__ = {
        'name': dict(builder=field, required=True),
        'in_': dict(key='in', builder=field, required=True),
        'description': dict(builder=field),
        'required': dict(builder=field),
        'deprecated': dict(builder=field),
        'allow_empty_value': dict(key='allowEmptyValue', builder=field),
        'style': dict(builder=field),
        'explode': dict(builder=field),
        'allow_reserved': dict(key='allowReserved', builder=field),
        'schema': dict(builder=child, child_builder=if_not_ref_else(Schema)),
        'example': dict(builder=field),
        'examples': dict(builder=child, child_builder=map_(if_not_ref_else(Example))),
    }


class Header(Parameter):
    __fields__ = {
        'name': dict(builder=field, restricted=True),
        'in_': dict(builder=field, restricted=True, default='header')
    }


class Encoding(Base2_v3_0_0):
    __fields__ = {
        'content_type': dict(key='contentType', builder=field),
        'headers': dict(builder=child, child_builder=map_(if_not_ref_else(Header))),
        'stype': dict(builder=field),
        'explode': dict(builder=field),
        'allow_reserved': dict(key='allowReserved', builder=field),
    }


class MediaType(Base2_v3_0_0):
    __fields__ = {
        'schema': dict(builder=child, child_builder=if_not_ref_else(Schema)),
        'example': dict(builder=field),
        'examples': dict(builder=child, child_builder=if_not_ref_else(Example)),
        'encoding': dict(builder=child, child_builder=map_(Encoding)),
    }


Parameter.attach_field('content', builder=child, child_builder=map_(MediaType))


class RequestBody(Base2_v3_0_0):
    __fields__ = {
        'description': dict(builder=field),
        'content': dict(builder=child, child_builder=map_(MediaType), required=True),
        'required': dict(builder=field),
    }


class Link(Base2_v3_0_0):
    __fields__ = {
        'operation_ref': dict(key='operationRef', builder=field),
        'operation_id': dict(key='operationId', builder=field),
        'parameters': dict(builder=child, child_builder=map_(is_str)),
        'request_body': dict(key='requestBody', builder=field),
        'description': dict(builder=field),
        'server': dict(builder=child, child_builder=Server),
    }


class Response(Base2_v3_0_0):
    __fields__ = {
        'description': dict(builder=field, required=True),
        'headers': dict(builder=child, child_builder=map_(if_not_ref_else(Header))),
        'content': dict(builder=child, child_builder=map_(MediaType)),
        'links': dict(builder=child, child_builder=map_(if_not_ref_else(Link))),
    }


class OAuthFlow(Base2_v3_0_0):
    __fields__ = {
        'authorization_url': dict(key='authorizationUrl', builder=field, required=True),
        'token_url': dict(key='tokenUrl', builder=field, required=True),
        'refresh_url': dict(key='refreshUrl', builder=field),
        'scopes': dict(builder=child, child_builder=map_(is_str), required=True),
    }


class OAuthFlows(Base2_v3_0_0):
    __fields__ = {
        'implicit': dict(builder=child, child_builder=OAuthFlow),
        'password': dict(builder=child, child_builder=OAuthFlow),
        'client_credentials': dict(key='clientCredentials', builder=child, child_builder=OAuthFlow),
        'authorization_code': dict(key='authorizationCode', builder=child, child_builder=OAuthFlow),

    }


class SecurityScheme(Base2_v3_0_0):
    __fields__ = {
        'type_': dict(key='type', builder=field, required=True),
        'description': dict(builder=field),
        'name': dict(builder=field),
        'in_': dict(key='in', builder=field),
        'scheme': dict(builder=field),
        'bearer_format': dict(builder=field),
        'flows': dict(builder=child, child_builder=OAuthFlows),
        'openid_connect_url': dict(builder=field),
    }


class Operation(Base2_v3_0_0):
    __fields__ = {
        'tags': dict(builder=child, child_builder=list_(is_str)),
        'summary': dict(builder=field),
        'description': dict(builder=field),
        'external_docs': dict(key='externalDocs', builder=child, child_builder=ExternalDocumentation),
        'operationId': dict(builder=field),
        'parameters': dict(builder=child, child_builder=list_(if_not_ref_else(Parameter))),
        'requestBody': dict(builder=child, child_builder=if_not_ref_else(RequestBody)),
        'responses': dict(builder=child, child_builder=map_(if_not_ref_else(Response))),
        'deprecated': dict(builder=field),
        'security': dict(builder=child, child_builder=list_(map_(list_(is_str)))),
        'servers': dict(builder=child, child_builder=list_(Server)),
    }


class PathItem(Base2_v3_0_0):
    __fields__ = {
        'ref': dict(key='$ref', builder=field),
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
        'parameters': dict(builder=child, child_builder=list_(if_not_ref_else(Parameter))),
    }

Operation.attach_field('callbacks', builder=child, child_builder=map_(if_not_ref_else(map_(PathItem))))


class Components(Base2_v3_0_0):
    __fields__ = {
        'schemas': dict(builder=child, child_builder=map_(Schema)),
        'responses': dict(builder=child, child_builder=map_(Response)),
        'parameters': dict(builder=child, child_builder=map_(Parameter)),
        'examples': dict(builder=field),
        'requestBodies': dict(builder=child, child_builder=map_(RequestBody)),
        'headers': dict(builder=child, child_builder=map_(Header)),
        'securitySchemes': dict(builder=child, child_builder=map_(SecurityScheme)),
        'links': dict(builder=child, child_builder=map_(Link)),
        'callbacks': dict(builder=child, child_builder=map_(map_(PathItem))),
    }


class Tag(Base2_v3_0_0):
    __fields__ = {
        'name': dict(builder=field, required=True),
        'description': dict(builder=field),
        'external_docs': dict(key='externalDocs', builder=child, child_builder=ExternalDocumentation),
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
        'external_docs': dict(key='externalDocs', builder=child, child_builder=ExternalDocumentation),
    }

