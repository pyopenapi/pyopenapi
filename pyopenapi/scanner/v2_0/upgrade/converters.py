from __future__ import absolute_import
from ....utils import jp_compose
from ....errs import SchemaError
from .constants import BASE_SCHEMA_FIELDS, SCHEMA_FIELDS
import six

def _generate_fields(obj, names):
    ret = {}
    for n in names:
        v = getattr(obj, n, None)
        if v:
            ret[n] = v

    return ret

def _patch_local_ref(ref, is_body=False):
    if not (ref and isinstance(ref, six.string_types)):
        return ref
    if not ref.startswith('#'):
        return ref

    if ref.startswith('#/definitions'):
        return ref.replace('#/definitions', '#/components/schemas', 1)
    elif ref.startswith('#/parameters'):
        return ref.replace(
            '#/parameters',
            '#/components/requestBodies' if is_body else '#/components/parameters',
            1
        )
    elif ref.startswith('#/responses'):
        return ref.replace('#/responses', '#/components/responses', 1)
    elif ref.startswith('#/paths/') and ref.find('parameters') != -1 and is_body:
        return ref.replace('parameters', 'requestBody', 1)

    return ref

def to_tag(obj, path):
    ret = {}
    ret['name'] = obj.name
    ret.update(_generate_fields(obj, [
        'description'
    ]))

    if obj.externalDocs:
        ret['externalDocs'] = to_external_docs(obj.externalDocs, jp_compose('externalDocs', base=path))

    return ret

def to_xml(obj, path):
    ret = {}
    ret.update(_generate_fields(obj, [
        'name',
        'namespace',
        'prefix',
        'attribute',
        'wrapped',
    ]))

    return ret

def to_external_docs(obj, path):
    ret = {}
    ret['url'] = obj.url
    if obj.description:
        ret['description'] = obj.description

    return ret

def from_items(obj, path):
    # TODO: raise a warning for unsupported collectionformat in items in 3.0

    ref = getattr(obj, 'original_ref', None)
    if ref:
        return {'$ref': _patch_local_ref(ref)}

    ret = {}
    ret.update(_generate_fields(obj, BASE_SCHEMA_FIELDS))
    if obj.items:
        ret['items'] = from_items(obj.items, jp_compose([path, 'items']))

    return ret

def to_schema(obj, path, items_converter=None):
    ref = getattr(obj, 'original_ref', None)
    if ref:
        return {'$ref': _patch_local_ref(ref)}

    if getattr(obj, 'type', None) == 'file':
        return {
            'type': 'string',
            'format': 'binary'
        }

    items_converter = items_converter or to_schema

    ret = {}
    ret.update(_generate_fields(obj, SCHEMA_FIELDS))

    required = getattr(obj, 'required', None)
    if isinstance(required, list) and len(required) > 0:
        ret['required'] = required

    all_of = getattr(obj, 'allOf', None)
    if all_of:
        target = ret.setdefault('allOf', [])
        for index, o in enumerate(all_of):
            target.append(to_schema(o, jp_compose(['allOf', str(index)], base=path)))

    items = getattr(obj, 'items', None)
    if items:
        ret['items'] = items_converter(items, jp_compose('items', base=path))

    properties = getattr(obj, 'properties', None)
    if properties:
        target = ret.setdefault('properties', {})
        for name, prop in six.iteritems(properties):
            target[name] = to_schema(prop, jp_compose(['properties', name], base=path), items_converter=items_converter)

    additional_properties = getattr(obj, 'additionalProperties', None)
    if isinstance(additional_properties, bool):
        if additional_properties is False:
            ret['additionalProperties'] = additional_properties
    elif additional_properties is not None:
        ret['additionalProperties'] = to_schema(additional_properties, jp_compose('additionalProperties', base=path))

    discriminator = getattr(obj, 'discriminator', None)
    if discriminator:
        ret['discriminator'] = {'propertyName': discriminator}

    _xml = getattr(obj, 'xml', None)
    if _xml:
        ret['xml'] = to_xml(_xml, jp_compose('xml', base=path))

    external_docs = getattr(obj, 'externalDocs', None)
    if external_docs:
        ret['externalDocs'] = to_external_docs(external_docs, jp_compose('externalDocs', base=path))

    return ret

def to_flows(obj, path):
    if not obj.flow:
        raise SchemaError('no flow type for oauth2, {}'.format(path))

    ret = {}
    flow = ret.setdefault(obj.flow, {})
    flow.update(_generate_fields(obj, [
        'authorizationUrl',
        'tokenUrl',
        'scopes',
    ]))

    return ret

def to_security_scheme(obj, path):
    ret = {}
    type_ = getattr(obj, 'type', None)
    ret['type'] = type_
    if type_ == 'basic':
        ret['scheme'] = 'basic'
    elif type_ == 'oauth2':
        ret['flows'] = to_flows(obj, path)

    ret.update(_generate_fields(obj, [
        'description',
        'name',
        'in',
    ]))

    return ret
