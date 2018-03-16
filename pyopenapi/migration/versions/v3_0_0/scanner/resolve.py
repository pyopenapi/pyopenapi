# -*- coding: utf-8 -*-

from __future__ import absolute_import
import six

from .....utils import jp_compose, jr_split
from .....errs import JsonReferenceError
from ....scan import Dispatcher
from ..objects import (
    PathItem,
    Schema,
    Parameter,
    Header,
    Encoding,
    MediaType,
    Response,
    Operation,
    Reference,
    Components,
    SchemaOrReference,
    ParameterOrReference,
    HeaderOrReference,
    ResponseOrReference,
    ExampleOrReference,
    LinkOrReference,
    RequestBodyOrReference,
    SecuritySchemeOrReference,
    CallbackOrReference,
)
from ..attrs import (
    ReferenceAttributeGroup,
    PathItemAttributeGroup,
)


def _resolve(obj, expected, app, path):
    if not obj:
        return

    if not isinstance(obj, (Reference, PathItem)):
        return

    attrs = obj.get_attrs('migration', ReferenceAttributeGroup if isinstance(
        obj, Reference) else PathItemAttributeGroup)

    if not attrs.normalized_ref:
        if isinstance(obj, Reference):
            raise JsonReferenceError('empty normalized_ref for {} in {}'.format(
                obj.ref, path))
        return

    resolved, new_ref = app.resolve_obj(
        attrs.normalized_ref,
        from_spec_version=app.original_spec_version
        if app.original_spec_version == '3.0.0' else '2.0',
        parser=expected,
        to_spec_version='3.0.0',
        remove_dummy=True,
    )
    if not resolved:
        raise JsonReferenceError('Unable to resolve: {}'.format(
            obj.normalized_ref))

    if obj.ref.startswith('#'):
        _, obj.ref = jr_split(new_ref)
    else:
        obj.ref = new_ref

    attrs.normalized_ref = new_ref
    attrs.ref_obj = resolved


class Resolve(object):
    """ pre-resolve 'normalized_ref' """

    class Disp(Dispatcher):
        pass

    def __init__(self, app):
        self.app = app

    @Disp.register([PathItem])
    def _path_item(self, path, obj):
        _resolve(obj, PathItem, self.app, path)
        # parameters
        for idx, param in enumerate(obj.parameters or []):
            _resolve(param, ParameterOrReference, self.app,
                     jp_compose([path, 'parameters',
                                 str(idx)]))

    @Disp.register([Schema])
    def _schema(self, path, obj):
        # allOf, oneOf, anyOf

        for idx, schema in enumerate(obj.all_of or []):
            _resolve(schema, SchemaOrReference, self.app,
                     jp_compose([path, 'allOf', str(idx)]))

        for idx, schema in enumerate(obj.one_of or []):
            _resolve(schema, SchemaOrReference, self.app,
                     jp_compose([path, 'oneOf', str(idx)]))

        for idx, schema in enumerate(obj.any_of or []):
            _resolve(schema, SchemaOrReference, self.app,
                     jp_compose([path, 'anyOf', str(idx)]))

        # not
        _resolve(obj.not_, SchemaOrReference, self.app,
                 jp_compose([path, 'not']))

        # items
        _resolve(obj.items, SchemaOrReference, self.app,
                 jp_compose([path, 'items']))

        # properties
        for k, schema in six.iteritems(obj.properties or {}):
            _resolve(schema, SchemaOrReference, self.app,
                     jp_compose([path, 'properties', k]))

        # additionalProperties
        if not isinstance(obj.additional_properties, bool):
            _resolve(obj.additional_properties, SchemaOrReference, self.app,
                     jp_compose([path, 'additionalProperties']))

    @Disp.register([Parameter, Header])
    def _parameter(self, path, obj):
        # schema field
        _resolve(obj.schema, SchemaOrReference, self.app,
                 jp_compose([path, 'schema']))

        # examples field
        for k, example in six.iteritems(obj.examples or {}):
            _resolve(example, ExampleOrReference, self.app,
                     jp_compose([path, 'examples', k]))

    @Disp.register([Encoding])
    def _encoding(self, path, obj):
        # headers field
        for k, header in six.iteritems(obj.headers or {}):
            _resolve(header, HeaderOrReference, self.app,
                     jp_compose([path, 'headers', k]))

    @Disp.register([MediaType])
    def _media_type(self, path, obj):
        # schema field
        _resolve(obj.schema, SchemaOrReference, self.app,
                 jp_compose([path, 'schema']))

        # examples field
        for k, example in six.iteritems(obj.examples or {}):
            _resolve(example, ExampleOrReference, self.app,
                     jp_compose([path, 'examples', k]))

    @Disp.register([Response])
    def _response(self, path, obj):
        # headers
        for k, header in six.iteritems(obj.headers or {}):
            _resolve(header, HeaderOrReference, self.app,
                     jp_compose([path, 'headers', k]))

        # links
        for k, link_ in six.iteritems(obj.links or {}):
            _resolve(link_, LinkOrReference, self.app,
                     jp_compose([path, 'links', k]))

    @Disp.register([Operation])
    def _operation(self, path, obj):
        # parameters

        for idx, param in enumerate(obj.parameters or []):
            _resolve(param, ParameterOrReference, self.app,
                     jp_compose([path, 'parameters',
                                 str(idx)]))

        # requestBody
        _resolve(obj.request_body, RequestBodyOrReference, self.app,
                 jp_compose([path, 'requestBody']))

        # responses
        for k, resp in six.iteritems(obj.responses or {}):
            _resolve(resp, ResponseOrReference, self.app,
                     jp_compose([path, 'responses', k]))

        # callbacks
        for k, callback in six.iteritems(obj.callbacks or {}):
            _resolve(callback, CallbackOrReference, self.app,
                     jp_compose([path, 'callbacks', k]))

    @Disp.register([Components])
    def _components(self, path, obj):
        # schemas
        for k, schema in six.iteritems(obj.schemas or {}):
            _resolve(schema, SchemaOrReference, self.app,
                     jp_compose([path, 'schemas', k]))

        # responses
        for k, resp in six.iteritems(obj.responses or {}):
            _resolve(resp, ResponseOrReference, self.app,
                     jp_compose([path, 'responses', k]))

        # parameters
        for k, param in six.iteritems(obj.parameters or {}):
            _resolve(param, ParameterOrReference, self.app,
                     jp_compose([path, 'parameters', k]))

        # examples
        for k, example in six.iteritems(obj.examples or {}):
            _resolve(example, ExampleOrReference, self.app,
                     jp_compose([path, 'examples', k]))

        # requestBodies
        for k, body in six.iteritems(obj.request_bodies or {}):
            _resolve(body, RequestBodyOrReference, self.app,
                     jp_compose([path, 'requestBodies', k]))

        # headers
        for k, header in six.iteritems(obj.headers or {}):
            _resolve(header, HeaderOrReference, self.app,
                     jp_compose([path, 'headers', k]))

        # securitySchemes
        for k, sec in six.iteritems(obj.security_schemes or {}):
            _resolve(sec, SecuritySchemeOrReference, self.app,
                     jp_compose([path, 'securitySchemes', k]))

        # links
        for k, link_ in six.iteritems(obj.links or {}):
            _resolve(link_, LinkOrReference, self.app,
                     jp_compose([path, 'links', k]))

        # callbacks
        for k, callback in six.iteritems(obj.callbacks or {}):
            _resolve(callback, CallbackOrReference, self.app,
                     jp_compose([path, 'callbacks', k]))
