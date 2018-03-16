# -*- coding: utf-8 -*-

from __future__ import absolute_import
import six

from ...spec import Base2, rename, child, list_, map_


def is_str(spec, path, override):
    if override:
        raise Exception('attemp to override "str" in {}'.format(path))
    if isinstance(spec, six.string_types):
        return spec
    raise Exception('should be a string, not {}, {}'.format(
        str(type(spec)), path))


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


# pylint: disable=invalid-name
class BaseObj_v2_0(Base2):
    __swagger_version__ = '2.0'


class Reference(BaseObj_v2_0):
    """ $ref
    """
    __fields__ = {
        '$ref': dict(readonly=False),
    }

    __internal__ = {
        'ref': dict(key='$ref', builder=rename),
    }


class XMLObject(BaseObj_v2_0):
    """ XML Object
    """
    __fields__ = {
        'name': dict(),
        'namespace': dict(),
        'prefix': dict(),
        'attribute': dict(),
        'wrapped': dict(),
    }


class ExternalDocumentation(BaseObj_v2_0):
    """ External Documentation Object
    """

    __fields__ = {
        'description': dict(),
        'url': dict(),
    }


class Tag(BaseObj_v2_0):
    """ Tag Object
    """
    __fields__ = {
        'name': dict(),
        'description': dict(),
    }

    __children__ = {
        'externalDocs': dict(child_builder=ExternalDocumentation),
    }

    __renamed__ = {
        'external_docs': dict(key='externalDocs'),
    }


class BaseSchema(BaseObj_v2_0):
    """ Base type for Items, Schema, Parameter, Header
    """

    __fields__ = {
        'type': dict(),
        'format': dict(),
        'default': dict(),
        'maximum': dict(),
        'exclusiveMaximum': dict(),
        'minimum': dict(),
        'exclusiveMinimum': dict(),
        'maxLength': dict(),
        'minLength': dict(),
        'maxItems': dict(),
        'minItems': dict(),
        'multipleOf': dict(),
        'enum': dict(),
        'pattern': dict(),
        'uniqueItems': dict(),
    }

    __renamed__ = {
        'type_': dict(key='type'),
        'format_': dict(key='format'),
        'exclusive_maximum': dict(key='exclusiveMaximum'),
        'exclusive_minimum': dict(key='exclusiveMinimim'),
        'max_length': dict(key='max_length'),
        'min_length': dict(key='min_length'),
        'max_items': dict(key='max_items'),
        'min_items': dict(key='min_items'),
        'multiple_of': dict(key='multipleOf'),
        'unique_items': dict(key='uniqueItems'),
    }


class Items(BaseSchema):
    """ Items Object
    """

    __fields__ = {
        'collectionFormat': dict(default='csv'),
    }

    __renamed__ = {
        'collection_format': dict(key='collectionFormat'),
    }


Items.attach_field('items', builder=child, child_builder=Items)


class Schema(BaseSchema):
    """ Schema Object
    """
    __fields__ = {
        '$ref': dict(readonly=False),
        'maxProperties': dict(),
        'minProperties': dict(),
        'title': dict(),
        'description': dict(),
        'discriminator': dict(),
        'readOnly': dict(),
        'example': dict(),
        'required': dict(default=[]),
    }

    __children__ = {
        'xml': dict(child_builder=XMLObject),
        'externalDocs': dict(child_builder=ExternalDocumentation),
    }

    __internal__ = {
        'ref': dict(key='$ref', builder=rename),
        'max_properties': dict(key='maxProperties', builder=rename),
        'min_properties': dict(key='minProperties', builder=rename),
        'read_only': dict(key='readOnly', builder=rename),
        'external_docs': dict(key='externalDocs', builder=rename),
        'all_of': dict(key='allOf', builder=rename),
        'additional_properties': dict(
            key='additionalProperties', builder=rename),
    }


BoolOrSchema = if_not_bool_else(Schema)

Schema.attach_field('items', builder=child, child_builder=Schema)
Schema.attach_field('allOf', builder=child, child_builder=list_(Schema))
Schema.attach_field('properties', builder=child, child_builder=map_(Schema))
Schema.attach_field(
    'additionalProperties', builder=child, child_builder=BoolOrSchema)


class Contact(BaseObj_v2_0):
    """ Contact Object
    """
    __fields__ = {
        'name': dict(),
        'url': dict(),
        'email': dict(),
    }


class License(BaseObj_v2_0):
    """ License Object
    """
    __fields__ = {
        'name': dict(),
        'url': dict(),
    }


class Info(BaseObj_v2_0):
    """ Info Object
    """
    __fields__ = {
        'version': dict(),
        'title': dict(),
        'description': dict(),
        'termsOfService': dict(),
    }

    __children__ = {
        'contact': dict(child_builder=Contact),
        'license': dict(child_builder=License),
    }

    __internal__ = {
        'terms_of_service': dict(key='termsOfService', builder=rename),
    }


class Parameter(BaseSchema):
    """ Parameter Object
    """
    __fields__ = {
        'name': dict(),
        'in': dict(),
        'required': dict(),
        'collectionFormat': dict(default='csv'),
        'description': dict(),
        'allowEmptyValue': dict(),
    }

    __children__ = {
        'schema': dict(child_builder=Schema),
        'items': dict(child_builder=Items),
    }

    __internal__ = {
        'in_': dict(key='in', builder=rename),
        'collection_format': dict(key='collectionFormat', builder=rename),
        'allow_empty_value': dict(key='allowEmptyValue', builder=rename),
    }


ParameterOrReference = if_not_ref_else(Parameter)


class Header(BaseSchema):
    """ Header Object
    """
    __fields__ = {
        'collectionFormat': dict(default='csv'),
        'description': dict(),
    }

    __children__ = {
        'items': dict(child_builder=Items),
    }

    __internal__ = {
        'collection_format': dict(key='collectionFormat', builder=rename),
    }


class Response(BaseObj_v2_0):
    """ Response Object
    """
    __fields__ = {
        'description': dict(),
        'examples': dict(),
    }

    __children__ = {
        'schema': dict(child_builder=Schema),
        'headers': dict(child_builder=map_(Header)),
    }


ResponseOrReference = if_not_ref_else(Response)
MapOfResponseOrReference = map_(ResponseOrReference)


class Operation(BaseObj_v2_0):
    """ Operation Object
    """
    __fields__ = {
        'operationId': dict(),
        'deprecated': dict(),
        'description': dict(),
        'summary': dict(),
    }

    __children__ = {
        'tags': dict(child_builder=list_(is_str)),
        'consumes': dict(child_builder=list_(is_str)),
        'produces': dict(child_builder=list_(is_str)),
        'schemes': dict(child_builder=list_(is_str)),
        'parameters': dict(child_builder=list_(ParameterOrReference)),
        'responses': dict(child_builder=MapOfResponseOrReference),
        'security': dict(child_builder=list_(map_(list_(is_str)))),
        'externalDocs': dict(child_builder=ExternalDocumentation),
    }

    __internal__ = {
        'method': dict(),
        'url': dict(),
        'path': dict(),
        'base_path': dict(),
        'cached_schemes': dict(default=[]),
        'cached_consumes': dict(default=[]),
        'cached_produces': dict(default=[]),
        'cached_security': dict(),
        'operation_id': dict(key='operationId', builder=rename),
        'external_docs': dict(key='externalDocs', builder=rename),
    }


class PathItem(BaseObj_v2_0):
    """ Path Item Object
    """
    __fields__ = {
        '$ref': dict(readonly=False),
    }

    __children__ = {
        'get': dict(child_builder=Operation),
        'put': dict(child_builder=Operation),
        'post': dict(child_builder=Operation),
        'delete': dict(child_builder=Operation),
        'options': dict(child_builder=Operation),
        'head': dict(child_builder=Operation),
        'patch': dict(child_builder=Operation),
        'parameters': dict(child_builder=list_(ParameterOrReference)),
    }

    __internal__ = {
        'ref': dict(key='$ref', builder=rename),
    }


class SecurityScheme(BaseObj_v2_0):
    """ Security Scheme Object
    """
    __fields__ = {
        'type': dict(),
        'description': dict(),
        'name': dict(),
        'in': dict(),
        'flow': dict(),
        'authorizationUrl': dict(),
        'tokenUrl': dict(),
    }

    __children__ = {'scopes': dict(child_builder=map_(is_str))}

    __internal__ = {
        'type_': dict(key='type', builder=rename),
        'in_': dict(key='in', builder=rename),
    }


class Swagger(BaseObj_v2_0):
    """ Swagger Object
    """

    __fields__ = {
        'swagger': dict(),
        'host': dict(),
        'basePath': dict(),
    }

    __children__ = {
        'info': dict(child_builder=Info),
        'schemes': dict(child_builder=list_(is_str)),
        'consumes': dict(child_builder=list_(is_str)),
        'produces': dict(child_builder=list_(is_str)),
        'paths': dict(child_builder=map_(PathItem)),
        'definitions': dict(child_builder=map_(Schema)),
        'parameters': dict(child_builder=map_(Parameter)),
        'responses': dict(child_builder=map_(Response)),
        'securityDefinitions': dict(child_builder=map_(SecurityScheme)),
        'security': dict(child_builder=list_(list_(is_str))),
        'tags': dict(child_builder=list_(Tag)),
        'externalDocs': dict(child_builder=ExternalDocumentation),
    }

    __internal__ = {
        'base_path': dict(key='basePath', builder=rename),
        'security_definitions': dict(key='securityDefinitions', builder=rename),
        'external_docs': dict(key='externalDocs', builder=rename),
    }
