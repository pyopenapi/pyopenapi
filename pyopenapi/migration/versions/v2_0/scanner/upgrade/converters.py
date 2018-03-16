# -*- coding: utf-8 -*-

from __future__ import absolute_import
import six

from ......utils import jp_compose, deref
from ......errs import SchemaError
from .constants import BASE_SCHEMA_FIELDS, SCHEMA_FIELDS
from .parameter_context import ParameterContext


def _generate_fields(obj, names):
    ret = {}
    for name in names:
        val = getattr(obj, name, None)
        if val is not None:
            ret[name] = val

    return ret


def to_style_and_explode(collection_format, in_, type_, path):
    style = None
    explode = None
    if collection_format == 'csv':
        if in_ == 'query':
            style = 'form'
            explode = False
        elif in_ in ('path', 'header'):
            style = 'simple'
    elif collection_format == 'ssv':
        if in_ != 'query' or type_ != 'array':
            raise SchemaError('Unsupported style: ssv for {},{} {}'.format(
                in_, type_, path))
        style = 'spaceDelimited'
    elif collection_format == 'pipes':
        if in_ != 'query' or type_ != 'array':
            raise SchemaError('Unsupported style: pipes for {},{} {}'.format(
                in_, type_, path))
        style = 'pipeDelimited'
    elif collection_format == 'multi':
        if in_ == 'query':
            style = 'form'
            explode = True

    return style, explode


def to_tag(obj, path):
    ret = {}
    ret['name'] = obj.name
    ret.update(_generate_fields(obj, ['description']))

    if obj.externalDocs:
        ret['externalDocs'] = to_external_docs(obj.externalDocs,
                                               jp_compose(
                                                   'externalDocs', base=path))

    return ret


def to_xml(obj, _):
    ret = {}
    ret.update(
        _generate_fields(obj, [
            'name',
            'namespace',
            'prefix',
            'attribute',
            'wrapped',
        ]))

    return ret


def to_external_docs(obj, _):
    ret = {}
    ret['url'] = obj.url
    if obj.description:
        ret['description'] = obj.description

    return ret


def from_items(obj, path):
    # TODO: raise a warning for unsupported collectionformat in items in 3.0

    ref = getattr(obj, '$ref', None)
    if ref:
        return {'$ref': ref}

    ret = {}
    ret.update(_generate_fields(obj, BASE_SCHEMA_FIELDS))
    if obj.items:
        ret['items'] = from_items(obj.items, jp_compose([path, 'items']))

    return ret


def to_schema(obj, path, items_converter=None):
    ref = getattr(obj, '$ref', None)
    if ref:
        return {'$ref': ref}

    if getattr(obj, 'type', None) == 'file':
        return {'type': 'string', 'format': 'binary'}

    items_converter = items_converter or to_schema

    ret = {}
    ret.update(_generate_fields(obj, SCHEMA_FIELDS))

    required = getattr(obj, 'required', None)
    if isinstance(required, list) and required:
        ret['required'] = required

    all_of = getattr(obj, 'allOf', None)
    if all_of:
        target = ret.setdefault('allOf', [])
        for index, schema in enumerate(all_of):
            target.append(
                to_schema(schema, jp_compose(['allOf', str(index)], base=path)))

    items = getattr(obj, 'items', None)
    if items:
        ret['items'] = items_converter(items, jp_compose('items', base=path))

    properties = getattr(obj, 'properties', None)
    if properties:
        target = ret.setdefault('properties', {})
        for name, prop in six.iteritems(properties):
            target[name] = to_schema(
                prop,
                jp_compose(['properties', name], base=path),
                items_converter=items_converter)

    additional_properties = getattr(obj, 'additionalProperties', None)
    if isinstance(additional_properties, bool):
        if additional_properties is False:
            ret['additionalProperties'] = additional_properties
    elif additional_properties is not None:
        ret['additionalProperties'] = to_schema(additional_properties,
                                                jp_compose(
                                                    'additionalProperties',
                                                    base=path))

    discriminator = getattr(obj, 'discriminator', None)
    if discriminator:
        ret['discriminator'] = {'propertyName': discriminator}

    _xml = getattr(obj, 'xml', None)
    if _xml:
        ret['xml'] = to_xml(_xml, jp_compose('xml', base=path))

    external_docs = getattr(obj, 'externalDocs', None)
    if external_docs:
        ret['externalDocs'] = to_external_docs(external_docs,
                                               jp_compose(
                                                   'externalDocs', base=path))

    return ret


def to_flows(obj, path):
    if not obj.flow:
        raise SchemaError('no flow type for oauth2, {}'.format(path))

    ret = {}
    flow = ret.setdefault(obj.flow, {})
    flow.update(_generate_fields(obj, [
        'authorizationUrl',
        'tokenUrl',
    ]))

    if obj.scopes:
        flow['scopes'] = obj.scopes.dump()

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
        ret['schema']['items'] = from_items(obj.items,
                                            jp_compose('items', base=path))

    if obj.is_set('collectionFormat'):
        style, explode = to_style_and_explode(obj.collectionFormat, 'header',
                                              getattr(obj, 'type', None),
                                              jp_compose(
                                                  'collectionFormat',
                                                  base=path))
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
            'application/x-www-form-urlencoded', 'multipart/form-data'
    ]:
        ret['contentType'] = _decide_encoding_content_type(obj, path)
        if obj.is_set('collectionFormat'):
            style, explode = to_style_and_explode(obj.collectionFormat,
                                                  getattr(obj, 'in', None),
                                                  getattr(obj, 'type', None),
                                                  jp_compose(
                                                      'collectionFormat',
                                                      base=path))
            if style:
                ret['contentType'] = _decide_encoding_content_type(obj, path)
                ret['style'] = style
                if explode is not None:
                    ret['explode'] = explode

    return ret


def to_media_type(obj, content_type, existing, path):
    # parameter object need to merge several objects into one schema object
    ret = existing or {}
    resolved_obj = deref(obj)
    dst_schema = ret.setdefault('schema', {})
    if resolved_obj.required:
        dst_schema.setdefault('required', []).append(resolved_obj.name)
    properties = dst_schema.setdefault('properties', {})
    if resolved_obj.name in properties:
        raise SchemaError(
            'duplicated name of formData parameter: {}'.format(path))

    src_schema = getattr(
        resolved_obj, 'schema', None
    ) or resolved_obj  # if it's body parameter, we should use obj.schema
    prop = properties.setdefault(resolved_obj.name, {})
    prop.update(
        to_schema(
            obj if getattr(obj, '$ref', None) else src_schema,
            path,
            items_converter=from_items))
    if getattr(resolved_obj, 'allowEmptyValue', None) is True:
        prop['nullable'] = True

    encoding = to_encoding(src_schema, content_type, path)
    if encoding:
        ret.setdefault('encoding', {})[resolved_obj.name] = encoding

    return ret


def to_request_body(obj, existing_body, ctx, path):
    ret = existing_body or {}
    content = ret.setdefault('content', {})
    resolved_obj = deref(obj)
    if resolved_obj.required:
        ret['required'] = True

    content_types = ctx.get_valid_mime_type()
    if ctx.is_file or ctx.is_form:
        for type_ in content_types:
            existing_media_type = content.setdefault(type_, {})
            content[type_] = to_media_type(obj, type_, existing_media_type,
                                           path)
    elif ctx.is_body:
        if existing_body:
            raise SchemaError('multiple bodies found: {}'.format(path))

        ret.update(_generate_fields(resolved_obj, [
            'description',
        ]))

        for type_ in content_types:
            media_type = content.setdefault(type_, {})
            media_type['schema'] = to_schema(resolved_obj.schema,
                                             jp_compose('schema', base=path))
    else:
        raise SchemaError(
            'invalid parameter context: {},{},{} for request body: {}'.format(
                ctx.is_file, ctx.is_form, ctx.is_body, path))

    return ret


def to_parameter(obj, path):
    ret = {}
    ret.update(
        _generate_fields(obj, [
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
        ret.setdefault('schema', {})['items'] = from_items(
            obj.items, jp_compose('items', base=path))

    if obj.is_set('collectionFormat'):
        style, explode = to_style_and_explode(obj.collectionFormat, in_, type_,
                                              jp_compose(
                                                  'collectionFormat',
                                                  base=path))
        if style:
            ret['style'] = style
        if explode is not None:
            ret['explode'] = explode

    return ret


def from_parameter(obj, existing_body, consumes, path):
    ref_ = getattr(obj, '$ref', None)
    resolved_obj = deref(obj)

    ctx = ParameterContext(resolved_obj.name, consumes=consumes)
    in_ = getattr(resolved_obj, 'in', None)
    type_ = getattr(resolved_obj, 'type', None)

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
            is_file=getattr(deref(resolved_obj.schema), 'type', None) == 'file')
        ret = to_request_body(obj, existing_body, ctx, ref_ or path)
    else:
        if ref_:
            ret = {'$ref': ref_}
        else:
            ret = to_parameter(obj, path)

    return ret, ctx


def to_response(obj, produces, path):
    ref = getattr(obj, '$ref', None)
    resolved_obj = deref(obj)
    if ref and not resolved_obj.schema:
        return {'$ref': ref}

    # if we have to output 'schema' part, we need
    # to inline them here because 'produces' might
    # be different from where '$ref' points to.

    ret = {}
    ret.update(_generate_fields(resolved_obj, ['description']))

    if resolved_obj.schema:
        if not produces:
            # generate a default content-type
            type_ = getattr(resolved_obj.schema, 'type', None)
            produces = [
                'application/json' if type_ == 'object' else 'text/plain'
            ]

        content = ret.setdefault('content', {})
        type_ = getattr(resolved_obj.schema, 'type', None)
        if type_ == 'file':
            media_type = content.setdefault('application/octet-stream', {})
            media_type['type'] = 'string'
            media_type['format'] = 'binary'
        else:
            for type_ in produces:
                content[type_] = {
                    'schema':
                    to_schema(resolved_obj.schema,
                              jp_compose('schema', base=path))
                }

    # header
    if resolved_obj.headers:
        headers = ret.setdefault('headers', {})
        for k, header in six.iteritems(resolved_obj.headers or {}):
            headers[k] = to_header(header, jp_compose(
                ['headers', k], base=path))

    return ret


def to_operation(obj, body, root_url, path, produces=None, consumes=None):
    ret = {}
    ret.update(
        _generate_fields(obj, [
            'summary',
            'description',
            'operationId',
            'deprecated',
        ]))

    if obj.tags:
        ret['tags'] = obj.tags.dump()

    if obj.security:
        ret['security'] = obj.security.dump()

    # parameters
    if obj.parameters:
        parameters = None
        for index, param in enumerate(obj.parameters):
            new_path = jp_compose(['parameters', str(index)], base=path)
            new_p, pctx = from_parameter(param, body, obj.consumes or consumes,
                                         new_path)
            if pctx.is_body:
                body = new_p
            else:
                if not parameters:
                    parameters = ret.setdefault('parameters', [])
                parameters.append(new_p)

    if body:
        ret['requestBody'] = body

    # responses
    if obj.responses:
        responses = ret.setdefault('responses', {})
        for k, resp in six.iteritems(obj.responses):
            responses[k] = to_response(resp, obj.produces or produces,
                                       jp_compose(['responses', k], base=path))

    # externalDocs
    if obj.externalDocs:
        ret['externalDocs'] = to_external_docs(obj.externalDocs,
                                               jp_compose(
                                                   'externalDocs', base=path))

    # schemes
    if obj.schemes:
        servers = ret.setdefault('servers', [])
        for scheme in obj.schemes:
            parts = six.moves.urllib.parse.urlsplit(root_url)
            servers.append({
                'url':
                six.moves.urllib.parse.urlunsplit((scheme, ) + parts[1:])
            })

    return ret


def to_contact(obj, _):
    ret = _generate_fields(obj, ('name', 'url', 'email'))

    return ret


def to_license(obj, _):
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
    ret.update(_generate_fields(obj, ['description', 'termsOfService']))

    if obj.contact:
        ret['contact'] = to_contact(obj.contact, jp_compose(
            'contact', base=path))
    if obj.license:
        ret['license'] = to_license(obj.license, jp_compose(
            'license', base=path))

    return ret


def to_path_item(obj, root_url, path, consumes=None, produces=None):
    ret, reloc = {}, {}
    if obj.ref:
        ret['$ref'] = obj.get_attrs('migration').normalized_ref

    # parameters
    body = None
    if obj.parameters:
        consumes, parameters = consumes or [], None
        for index, param in enumerate(obj.parameters):
            new_p, pctx = from_parameter(
                param,
                body,
                consumes,
                path=jp_compose(['parameters', str(index)], base=path))
            if pctx.is_file or pctx.is_body:
                body = new_p
                reloc['parameters/{}'.format(
                    index)] = 'x-pyopenapi_internal_request_body'
            else:
                if not parameters:
                    parameters = ret.setdefault('parameters', [])
                parameters.append(new_p)

    # operations
    for method in (
            'get',
            'put',
            'post',
            'delete',
            'options',
            'head',
            'patch',
    ):
        operation = getattr(obj, method, None)
        if operation:
            ret[method] = to_operation(
                operation,
                body,
                root_url,
                jp_compose(method, base=path),
                produces=produces,
                consumes=consumes)

    if body:
        # Valid $ref for Parameter in Swagger 2.0 should only point
        # to 'parameters' field under Swagger object, therefore, there
        # should be no $ref point to here.
        #
        # This dumped field is only intended for debug only
        ret['x-pyopenapi_internal_request_body'] = body

    return ret, reloc


def from_swagger_to_server(obj, _):
    url = obj.host if not obj.basePath else six.moves.urllib.parse.urlunsplit(
        (obj.schemes[0]
         if obj.schemes else 'https', obj.host, obj.basePath, None, None))
    url = url or '/'

    return {'url': url}


def to_openapi(obj, path):
    ret = {'openapi': '3.0.0'}
    reloc = {}

    # info
    if obj.info:
        ret['info'] = to_info(obj.info, jp_compose('info', base=path))

    # servers
    server = from_swagger_to_server(obj, path)
    ret['servers'] = [server]

    # paths
    if obj.paths:
        paths = ret.setdefault('paths', {})
        for k, path_ in six.iteritems(obj.paths):
            if k.startswith('x-'):
                raise SchemaError(
                    'No more extension field in Paths object: {}'.format(path))

            paths[k], tmp_reloc = to_path_item(
                path_,
                server['url'],
                jp_compose(k, base=path),
                consumes=obj.consumes,
                produces=obj.produces)
            if tmp_reloc:
                reloc.setdefault('paths', {})[k.replace('~', '~0').replace(
                    '/', '~1')] = tmp_reloc

    # security
    if obj.security:
        ret['security'] = obj.security

    # tag
    if obj.tags:
        tags = ret.setdefault('tags', [])
        for index, tag in enumerate(obj.tags):
            tags.append(
                to_tag(tag, jp_compose(['tags', str(index)], base=path)))

    # externalDocs
    if obj.externalDocs:
        ret['externalDocs'] = to_external_docs(obj.externalDocs,
                                               jp_compose(
                                                   'externalDocs', base=path))

    if obj.definitions or obj.parameters or obj.responses or obj.securityDefinitions:
        components = ret.setdefault('components', {})

        # definitions
        if obj.definitions:
            schemas = components.setdefault('schemas', {})
            for k, schema in six.iteritems(obj.definitions):
                schemas[k] = to_schema(schema,
                                       jp_compose(
                                           ['definitions', k], base=path))

            reloc['definitions'] = 'components/schemas'

        # parameters
        if obj.parameters:
            parameters = None
            request_bodies = None
            param_reloc = {}
            for k, param in six.iteritems(obj.parameters):
                param, pctx = from_parameter(param, None, None,
                                             jp_compose(
                                                 ['parameters', k], base=path))
                if pctx.is_body:
                    if request_bodies is None:
                        request_bodies = components.setdefault(
                            'requestBodies', {})
                    request_bodies[k] = param
                    param_reloc[k] = '#/components/requestBodies/{}'.format(k)
                else:
                    if parameters is None:
                        parameters = components.setdefault('parameters', {})
                    parameters[k] = param

            param_reloc[''] = '#/components/parameters'
            reloc['parameters'] = param_reloc

        # responses
        if obj.responses:
            responses = components.setdefault('responses', {})
            for k, resp in six.iteritems(obj.responses):
                responses[k] = to_response(resp, obj.produces,
                                           jp_compose(
                                               ['responses', k], base=path))

            reloc['responses'] = 'components/responses'

        # securityDefinitions
        if obj.securityDefinitions:
            security_schemes = components.setdefault('securitySchemes', {})
            for k, sec in six.iteritems(obj.securityDefinitions):
                security_schemes[k] = to_security_scheme(
                    sec, jp_compose(['securityDefinitions', k], base=path))

            reloc['securityDefinitions'] = 'components/securitySchemes'

    return ret, reloc
