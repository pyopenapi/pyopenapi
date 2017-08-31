from __future__ import absolute_import
from ....utils import jp_compose, final, deref
from ....errs import SchemaError
from .constants import BASE_SCHEMA_FIELDS, SCHEMA_FIELDS, FILE_CONTENT_TYPES
from .parameter_context import ParameterContext
from os import path
import six


def _generate_fields(obj, names):
    ret = {}
    for n in names:
        v = getattr(obj, n, None)
        if v:
            ret[n] = v

    return ret

def _patch_local_ref(ref, parameter_context=None):
    if not (ref and isinstance(ref, six.string_types)):
        return ref
    if not ref.startswith('#'):
        return ref

    if ref.startswith('#/definitions'):
        return ref.replace('#/definitions', '#/components/schemas', 1)
    elif ref.startswith('#/parameters'):
        if not parameter_context.is_body:
            return ref.replace('#/parameters', '#/components/parameters', 1)

        # we need to guess a content type that would 100%
        # generated under #/components/requestBodies for
        # the referenced parameter
        return jp_compose([
            '#', 'components', 'requestBodies',
            ref[len('#/parameters/'):], # name part of original reference
            'content',
            parameter_context.get_default_mime_type(),
            'schema', 'properties',
            parameter_context.name
        ])
    elif ref.startswith('#/responses'):
        return ref.replace('#/responses', '#/components/responses', 1)

    return ref

def to_style_and_explode(collection_format, in_, type_, path):
    style = None
    explode = None
    if collection_format == 'csv':
        if in_ in ('query'):
            style = 'form'
            explode = False
        elif in_ in ('path', 'header'):
            style = 'simple'
    elif collection_format == 'ssv':
        if in_ != 'query' or type_ != 'array':
            raise SchemaError('Unsupported style: ssv for {},{} {}'.format(in_, type_, path))
        style = 'spaceDelimited'
    elif collection_format == 'pipes':
        if in_ != 'query' or type_ != 'array':
            raise SchemaError('Unsupported style: pipes for {},{} {}'.format(in_, type_, path))
        style = 'pipeDelimited'
    elif collection_format == 'multi':
         if in_ in ('query'):
            style = 'form'
            explode = True

    return style, explode

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

def to_schema(obj, path, items_converter=None, parameter_context=None):
    ref = getattr(obj, 'original_ref', None)
    if ref:
        return {'$ref': _patch_local_ref(ref, parameter_context=parameter_context)}

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

def to_header(obj, path):
    ret = {}
    ret.update(_generate_fields(obj, [
        'description',
    ]))
    ret['schema'] = _generate_fields(obj, BASE_SCHEMA_FIELDS)
    if obj.items:
        ret['schema']['items'] = from_items(obj.items, jp_compose('items', base=path))

    if obj.is_set('collectionFormat'):
        style, explode = to_style_and_explode(
            obj.collectionFormat,
            'header',
            getattr(obj, 'type', None),
            jp_compose('collectionFormat', base=path)
        )
        if style:
            ret['style'] = style
        if explode is not None:
            ret['explode'] = explode

    return ret

def _decide_encoding_content_type(obj, path):
    type_ = getattr(obj, 'type', None)
    if type_ == 'file':
        return 'application/octet-stream'
    if type_ == 'object':
        return 'application/json'
    if type_ == 'array':
        cur_type = type_
        cur_obj = obj
        cur_path = path
        while cur_type == 'array':
            cur_obj = cur_obj.items
            cur_type = getattr(cur_obj, 'type', None)
            cur_path = jp_compose('items', base=path)

        return _decide_encoding_content_type(cur_obj, cur_path)

    return 'text/plain'

def to_encoding(obj, content_type, path):
    ret = {}
    # TODO: support multipart/*
    if content_type in [
        'application/x-www-form-urlencoded',
        'multipart/form-data'
    ]:
        ret['contentType'] = _decide_encoding_content_type(obj, path)
        if obj.is_set('collectionFormat'):
            style, explode = to_style_and_explode(
                obj.collectionFormat,
                getattr(obj, 'in', None),
                getattr(obj, 'type', None),
                jp_compose('collectionFormat', base=path)
            )
            if style:
                ret['contentType'] = _decide_encoding_content_type(obj, path)
                ret['style'] = style
                if explode is not None:
                    ret['explode'] = explode

    return ret

def to_media_type(obj, content_type, existing, example, ctx, path):
    # parameter object need to merge several objects into one schema object
    ret = existing or {}
    src_schema = getattr(obj, 'schema', None) or obj # if it's body parameter, we should use obj.schema
    dst_schema = ret.setdefault('schema', {})
    if obj.required:
        dst_schema.setdefault('required', []).append(obj.name)
    properties = dst_schema.setdefault('properties', {})
    if obj.name in properties:
        raise SchemaError('duplicated name of formData parameter: {}'.format(path))
    prop = properties.setdefault(obj.name, {})
    prop.update(to_schema(src_schema, path, items_converter=from_items, parameter_context=ctx))
    if getattr(obj, 'allowEmptyValue', None) == True:
        prop['nullable'] = True

    encoding = to_encoding(src_schema, content_type, path)
    if encoding:
        ret.setdefault('encoding', {})[obj.name] = encoding

    return ret

def to_request_body(obj, existing_body, ctx, path):
    ret = existing_body or {}
    in_ = getattr(obj, 'in', None)
    type_ = getattr(obj, 'type', None)

    content = ret.setdefault('content', {})
    if obj.required:
        ret['required'] = True

    content_types = ctx.get_valid_mime_type()
    if ctx.is_file or in_ == 'formData':
        for c in content_types:
            existing_media_type = content.setdefault(c, {})
            content[c] = to_media_type(obj, c, existing_media_type, None, ctx, path)
    elif ctx.is_body:
        if existing_body:
            raise SchemaError('multiple bodies found: {}'.format(path))

        ret.update(_generate_fields(obj, [
            'description',
        ]))

        for c in content_types:
            media_type = content.setdefault(c, {})
            media_type['schema'] = to_schema(obj.schema, jp_compose('schema', base=path), parameter_context=ctx)
    else:
        raise SchemaError('unrecognized "in" parameter for request body: {}'.format(in_))

    return ret

def to_parameter(obj, ctx, path):
    ret = {}
    ret.update(_generate_fields(obj, [
        'description',
        'required',
        'allowEmptyValue',
    ]))

    type_ = getattr(obj, 'type', None)
    in_ = getattr(obj, 'in', None)

    schema_2_update = _generate_fields(obj, BASE_SCHEMA_FIELDS)
    if schema_2_update:
        ret['schema'] = schema_2_update
    ret['name'] = obj.name
    ret['in'] = in_
    if obj.items:
        ret.setdefault('schema', {})['items'] = from_items(obj.items, jp_compose('items', base=path))

    if obj.is_set('collectionFormat'):
        style, explode = to_style_and_explode(
            obj.collectionFormat,
            in_,
            type_,
            jp_compose('collectionFormat', base=path)
        )
        if style:
            ret['style'] = style
        if explode is not None:
            ret['explode'] = explode

    return ret

def from_parameter(obj, existing_body, consumes, path):
    ref_ = obj.original_ref
    resolved_obj = deref(obj)
    obj = final(obj)

    ctx = ParameterContext(obj.name, consumes=consumes)
    in_ = getattr(obj, 'in', None)
    type_ = getattr(obj, 'type', None)

    ret = None
    if type_ == 'file':
        ctx.update(is_body=True, is_file=True)
        ret = to_request_body(obj, existing_body, ctx, path)
    elif in_ == 'formData':
        ctx.update(is_body=True, is_form=True)
        ret = to_request_body(obj, existing_body, ctx, ref_ or path)
    elif in_ == 'body':
        ctx.update(
            is_body=True,
            is_file=getattr(deref(obj.schema), 'type', None) == 'file'
        )
        ret = to_request_body(obj, existing_body, ctx, ref_ or path)
    else:
        if ref_:
            ret = {'$ref': _patch_local_ref(ref_, parameter_context=ctx)}
        else:
            ret = to_parameter(obj, ctx, path)

    return ret, ctx

def to_response(obj, produces, path):
    if obj.original_ref:
        return {'$ref': _patch_local_ref(obj.original_ref)}

    ret = {}
    ret.update(_generate_fields(obj, [
        'description'
    ]))

    if obj.schema:
        if len(produces) == 0:
            raise SchemaError('unable to convert to content: no "produces" declared, {}'.format(path))

        content = ret.setdefault('content', {})
        type_ = getattr(obj.schema, 'type', None)
        if type_ == 'file':
            media_type = content.setdefault('application/octet-stream', {})
            media_type['type'] = 'string'
            media_type['format'] = 'binary'
        else:
            for p in produces:
                content[p] = {'schema': to_schema(obj.schema, jp_compose('schema', base=path))}

    # header
    if obj.headers:
        headers = ret.setdefault('headers', {})
        for k, v in six.iteritems(obj.headers or {}):
            headers[k] = to_header(v, jp_compose(['headers', k], base=path))

    return ret

def to_operation(obj, root_url, path):
    ret = {}
    ret.update(_generate_fields(obj, [
        'tags',
        'summary',
        'description',
        'operationId',
        'deprecated',
    ]))

    # we need to merge multiple form parameters into one body in 3.0.0
    body = None

    # parameters
    if obj.parameters:
        parameters = None
        for index, p in enumerate(obj.parameters):
            new_path = jp_compose(['parameters', str(index)], base=path)
            new_p, pctx = from_parameter(p, body, obj.consumes, new_path)
            if pctx.is_body:
                body = new_p
            else:
                if p._parent_ is not obj:
                    # for those parameters merged from PathItem and not body / file type,
                    # leave them in PathItem level
                    continue

                if not parameters:
                    parameters = ret.setdefault('parameters', [])
                parameters.append(new_p)

    if body:
        ret['requestBody'] = body

    # responses
    if obj.responses:
        responses = ret.setdefault('responses', {})
        for k, v in six.iteritems(obj.responses):
            responses[k] = to_response(v, obj.produces, jp_compose(['responses', k], base=path))

    # externalDocs
    if obj.externalDocs:
        ret['externalDocs'] = to_external_docs(obj.externalDocs, jp_compose('externalDocs', base=path))

    # schemes
    if obj.schemes:
        servers = ret.setdefault('servers', [])
        for s in obj.schemes:
            parts = six.moves.urllib.parse.urlsplit(root_url)
            servers.append({'url': six.moves.urllib.parse.urlunsplit((s,) + parts[1:])})

    # security
    if obj.security:
        ret['security'] = obj.security

    return ret

def to_contact(obj, path):
    ret = _generate_fields(obj, (
        'name',
        'url',
        'email'
    ))

    return ret

def to_license(obj, path):
    ret = {}
    ret['name'] = obj.name
    ret.update(_generate_fields(obj, ['url']))

    return ret

def to_info(obj, path):
    ret = {}

    # required fields
    ret['title'] = obj.title
    ret['version'] = obj.version

    # optional fields
    ret.update(_generate_fields(obj, [
        'description',
        'termsOfService'
    ]))

    if obj.contact:
        ret['contact'] = to_contact(obj.contact, jp_compose('contact', base=path))
    if obj.license:
        ret['license'] = to_license(obj.license, jp_compose('license', base=path))

    return ret

