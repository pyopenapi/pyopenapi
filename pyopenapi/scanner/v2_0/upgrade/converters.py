from __future__ import absolute_import
from ....utils import jp_compose
from .constants import BASE_SCHEMA_FIELDS
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

