from __future__ import absolute_import
from ..base2 import Base2, field, rename, child, list_, map_
import six


def is_str(spec, path):
    if isinstance(spec, six.string_types):
        return spec
    raise Exception('should be a string, not {}, {}'.format(str(type(spec)), path))

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


class BaseObj_v2_0(Base2):
    __swagger_version__ = '2.0'


class Reference(BaseObj_v2_0):
    """ $ref
    """
    __fields__ = {
        '$ref': dict(builder=field),
    }

    __renamed__ = {
        'ref': dict(key='$ref'),
    }

    __internal__ = {
        'ref_obj': dict(),
    }


class XMLObject(BaseObj_v2_0):
    """ XML Object
    """
    __fields__ = {
        'name': dict(builder=field),
        'namespace': dict(builder=field),
        'prefix': dict(builder=field),
        'attribute': dict(builder=field),
        'wrapped': dict(builder=field),
    }


class ExternalDocumentation(BaseObj_v2_0):
    """ External Documentation Object
    """

    __fields__ = {
        'description': dict(builder=field),
        'url': dict(builder=field),
    }


class Tag(BaseObj_v2_0):
    """ Tag Object
    """
    __fields__ = {
        'name': dict(builder=field),
        'description': dict(builder=field),
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
        'type': dict(builder=field),
        'format': dict(builder=field),
        'default': dict(builder=field),
        'maximum': dict(builder=field),
        'exclusiveMaximum': dict(builder=field),
        'minimum': dict(builder=field),
        'exclusiveMinimum': dict(builder=field),
        'maxLength': dict(builder=field),
        'minLength': dict(builder=field),
        'maxItems': dict(builder=field),
        'minItems': dict(builder=field),
        'multipleOf': dict(builder=field),
        'enum': dict(builder=field),
        'pattern': dict(builder=field),
        'uniqueItems': dict(builder=field),
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
        'collectionFormat': dict(builder=field, default='csv'),
    }

    __renamed__ = {
        'collection_format': dict(key='collectionFormat'),
    }

    def _prim_(self, v, prim_factory, ctx=None):
        return prim_factory.produce(self, v, ctx)


Items.attach_field('items', builder=child, child_builder=Items)


class Schema(BaseSchema):
    """ Schema Object
    """
    __fields__ = {
        '$ref': dict(builder=field),
        'maxProperties': dict(builder=field),
        'minProperties': dict(builder=field),
        'title': dict(builder=field),
        'description': dict(builder=field),
        'discriminator': dict(builder=field),
        'readOnly': dict(builder=field),
        'example': dict(builder=field),
        'required': dict(builder=field, default=[]),
    }

    __children__ = {
        'xml': dict(child_builder=XMLObject),
        'externalDocs': dict(child_builder=ExternalDocumentation),
    }

    __renamed__ = {
        'ref': dict(key='$ref'),
        'max_properties': dict(key='maxProperties'),
        'min_properties': dict(key='minProperties'),
        'read_only': dict(key='readOnly'),
        'external_docs': dict(key='externalDocs'),
        'all_of': dict(key='allOf'),
        'additional_properties': dict(key='additionalProperties'),
    }

    __internal__ = {
        'ref_obj': dict(),
        'final': dict(),
        'name': dict(),
        'normalized_ref': dict(),
    }

    def _prim_(self, v, prim_factory, ctx=None):
        return prim_factory.produce(self, v, ctx)

BoolOrSchema = if_not_bool_else(Schema)

Schema.attach_field('items', builder=child, child_builder=Schema)
Schema.attach_field('allOf', builder=child, child_builder=list_(Schema))
Schema.attach_field('properties', builder=child, child_builder=map_(Schema))
Schema.attach_field('additionalProperties', builder=child, child_builder=BoolOrSchema)


class Contact(BaseObj_v2_0):
    """ Contact Object
    """
    __fields__ = {
        'name': dict(builder=field),
        'url': dict(builder=field),
        'email': dict(builder=field),
    }


class License(BaseObj_v2_0):
    """ License Object
    """
    __fields__ = {
        'name': dict(builder=field),
        'url': dict(builder=field),
    }


class Info(BaseObj_v2_0):
    """ Info Object
    """
    __fields__ = {
        'version': dict(builder=field),
        'title': dict(builder=field),
        'description': dict(builder=field),
        'termsOfService': dict(builder=field),
    }

    __children__ = {
        'contact': dict(child_builder=Contact),
        'license': dict(child_builder=License),
    }

    __renamed__ = {
        'terms_of_service': dict(key='termsOfService'),
    }


class Parameter(BaseSchema):
    """ Parameter Object
    """
    __fields__ = {
        'name': dict(builder=field),
        'in':  dict(builder=field),
        'required': dict(builder=field),
        'collectionFormat': dict(builder=field, default='csv'),
        'description': dict(builder=field),
        'allowEmptyValue': dict(builder=field),
    }

    __children__ = {
        'schema': dict(child_builder=Schema),
        'items': dict(child_builder=Items),
    }

    __renamed__ = {
        'in_': dict(key='in'),
        'collection_format': dict(key='collectionFormat'),
        'allow_empty_value': dict(key='allowEmptyValue'),
    }

    __internal__ = {
        'ref_obj': dict(),
        'normalized_ref': dict(),
    }

    def _prim_(self, v, prim_factory, ctx=None):
        i = getattr(self, 'in')
        return prim_factory.produce(self.schema, v, ctx) if i == 'body' else prim_factory.produce(self, v, ctx)

ParameterOrReference = if_not_ref_else(Parameter)


class Header(BaseSchema):
    """ Header Object
    """
    __fields__ = {
        'collectionFormat': dict(builder=field, default='csv'),
        'description': dict(builder=field),
    }

    __children__ = {
        'items': dict(child_builder=Items),
    }

    __renamed__ = {
        'collection_format': dict(key='collectionFormat'),
    }

    def _prim_(self, v, prim_factory, ctx=None):
        return prim_factory.produce(self, v, ctx)


class Response(BaseObj_v2_0):
    """ Response Object
    """
    __fields__ = {
        'description': dict(builder=field),
        'examples': dict(builder=field),
    }

    __children__ = {
        'schema': dict(child_builder=Schema),
        'headers': dict(child_builder=map_(Header)),
    }

    __internal_fields__ = {
        'ref_obj': None,
        'normalized_ref': None,
    }

ResponseOrReference = if_not_ref_else(Response)


class Operation(BaseObj_v2_0):
    """ Operation Object
    """
    __fields__ = {
        'operationId': dict(builder=field),
        'deprecated': dict(builder=field),
        'description': dict(builder=field),
        'summary': dict(builder=field),
    }

    __children__ = {
        'tags': dict(child_builder=list_(is_str)),
        'consumes': dict(child_builder=list_(is_str)),
        'produces': dict(child_builder=list_(is_str)),
        'schemes': dict(child_builder=list_(is_str)),
        'parameters': dict(child_builder=list_(ParameterOrReference)),
        'responses': dict(child_builder=map_(ResponseOrReference)),
        'security': dict(child_builder=list_(map_(list_(is_str)))),
        'externalDocs': dict(child_builder=ExternalDocumentation),
    }

    __renamed__ = {
        'operation_id': dict(key='operationId'),
        'external_docs': dict(key='externalDocs'),
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
    }

    def __call__(self, **k):
        # prepare parameter set
        params = dict(header={}, query=[], path={}, body={}, formData=[], file={})
        names = []
        def _convert_parameter(p):
            if p.name not in k and not p.is_set("default") and p.required:
                raise ValueError('requires parameter: ' + p.name)

            if p.is_set("default"):
                v = k.get(p.name, p.default)
            else:
                if p.name in k:
                    v = k[p.name]
                else:
                    # do not provide value for parameters that use didn't specify.
                    return

            c = p._prim_(v, self._prim_factory, ctx=dict(read=False))
            i = getattr(p, 'in')

            if p.type == 'file':
                params['file'][p.name] = c
            elif i in ('query', 'formData'):
                if isinstance(c, Array):
                    if p.items.type == 'file':
                        params['file'][p.name] = c
                    else:
                        params[i].extend([tuple([p.name, v]) for v in c.to_url()])
                else:
                    params[i].append((p.name, str(c),))
            else:
                params[i][p.name] = str(c) if i != 'body' else c

            names.append(p.name)

        for p in self.parameters:
            _convert_parameter(final(p))

        # check for unknown parameter
        unknown = set(six.iterkeys(k)) - set(names)
        if len(unknown) > 0:
            raise ValueError('Unknown parameters: {0}'.format(unknown))

        return \
        Request(op=self, params=params), _Response(self)


class PathItem(BaseObj_v2_0):
    """ Path Item Object
    """
    __fields__ = {
        '$ref': dict(builder=field),
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
        'ref_obj': dict(),
        'normalized_ref': dict(),
    }

    __renamed__ = {
        'ref': dict(key='$ref'),
    }


class SecurityScheme(BaseObj_v2_0):
    """ Security Scheme Object
    """
    __fields__ = {
        'type': dict(builder=field),
        'description': dict(builder=field),
        'name': dict(builder=field),
        'in': dict(builder=field),
        'flow': dict(builder=field),
        'authorizationUrl': dict(builder=field),
        'tokenUrl': dict(builder=field),
    }

    __children__ = {
        'scopes': dict(child_builder=map_(is_str))
    }

    __renamed__ = {
        'type_': dict(key='type'),
        'in_': dict(key='in'),
    }


class Swagger(BaseObj_v2_0):
    """ Swagger Object
    """

    __fields__ = {
        'swagger': dict(builder=field),
        'host': dict(builder=field),
        'basePath': dict(builder=field),
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

    __renamed__ = {
        'base_path': dict(key='basePath'),
        'security_definitions': dict(key='securityDefinitions'),
        'external_docs': dict(key='externalDocs'),
    }

