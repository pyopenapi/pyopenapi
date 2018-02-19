from __future__ import absolute_import
from ....utils import jp_compose, jr_split
from ....errs import ReferenceError
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
    Example,
    Link,
    RequestBody,
    Components,
    SecurityScheme,

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
import six

def _resolve(o, expected, app, path):
    if not o:
        return

    if not isinstance(o, (Reference, PathItem)):
        return

    if not o.normalized_ref:
        if isinstance(o, Reference):
            raise ReferenceError('empty normalized_ref for {} in {}'.format(o.ref, path))
        return

    ro, new_ref = app.resolve_obj(
        o.normalized_ref,
        from_spec_version='2.0',
        parser=expected,
        to_spec_version='3.0.0',
        remove_dummy=True,
    )
    if not ro:
        raise ReferenceError('Unable to resolve: {}'.format(o.normalized_ref))

    if o.ref.startswith('#'):
        _, o.ref = jr_split(new_ref)
    else:
        o.ref = new_ref

    o.normalized_ref = new_ref
    o.ref_obj = ro


class Resolve(object):
    """ pre-resolve 'normalized_ref' """

    class Disp(Dispatcher): pass

    def __init__(self, app):
        self.app = app

    @Disp.register([PathItem])
    def _path_item(self, path, obj):
        _resolve(obj, PathItem, self.app, path)
        # parameters
        [_resolve(
            s, ParameterOrReference, self.app, jp_compose([path, 'parameters', str(idx)])
        ) for idx, s in enumerate(obj.parameters or [])]

    @Disp.register([Schema])
    def _schema(self, path, obj):
        # allOf, oneOf, anyOf
        [_resolve(s, SchemaOrReference, self.app, jp_compose([path, 'allOf', str(idx)])) for idx, s in enumerate(obj.all_of or [])]
        [_resolve(s, SchemaOrReference, self.app, jp_compose([path, 'oneOf', str(idx)])) for idx, s in enumerate(obj.one_of or [])]
        [_resolve(s, SchemaOrReference, self.app, jp_compose([path, 'anyOf', str(idx)])) for idx, s in enumerate(obj.any_of or [])]

        # not
        _resolve(obj.not_, SchemaOrReference, self.app, jp_compose([path, 'not']))

        # items
        _resolve(obj.items, SchemaOrReference, self.app, jp_compose([path, 'items']))

        # properties
        for k, v in six.iteritems(obj.properties or {}):
            _resolve(v, SchemaOrReference, self.app, jp_compose([path, 'properties', k]))

        # additionalProperties
        if not isinstance(obj.additional_properties, bool):
            _resolve(obj.additional_properties, SchemaOrReference, self.app, jp_compose([path, 'additionalProperties']))

    @Disp.register([Parameter, Header])
    def _parameter(self, path, obj):
        # schema field
        _resolve(obj.schema, SchemaOrReference, self.app, jp_compose([path, 'schema']))

        # examples field
        for k, v in six.iteritems(obj.examples or {}):
            _resolve(v, ExampleOrReference, self.app, jp_compose([path, 'examples', k]))

    @Disp.register([Encoding])
    def _encoding(self, path, obj):
        # headers field
        for k, v in six.iteritems(obj.headers or {}):
            _resolve(v, HeaderOrReference, self.app, jp_compose([path, 'headers', k]))

    @Disp.register([MediaType])
    def _media_type(self, path, obj):
        # schema field
        _resolve(obj.schema, SchemaOrReference, self.app, jp_compose([path, 'schema']))

        # examples field
        for k, v in six.iteritems(obj.examples or {}):
            _resolve(v, ExampleOrReference, self.app, jp_compose([path, 'examples', k]))

    @Disp.register([Response])
    def _response(self, path, obj):
        # headers
        for k, v in six.iteritems(obj.headers or {}):
            _resolve(v, HeaderOrReference, self.app, jp_compose([path, 'headers', k]))

        # links
        for k, v in six.iteritems(obj.links or {}):
            _resolve(v, LinkOrReference, self.app, jp_compose([path, 'links', k]))

    @Disp.register([Operation])
    def _operation(self, path, obj):
        # parameters
        [_resolve(
            s, ParameterOrReference, self.app, jp_compose([path, 'parameters', str(idx)])
        ) for idx, s in enumerate(obj.parameters or [])]

        # requestBody
        _resolve(obj.request_body, RequestBodyOrReference, self.app, jp_compose([path, 'requestBody']))

        # responses
        for k, v in six.iteritems(obj.responses or {}):
            _resolve(v, ResponseOrReference, self.app, jp_compose([path, 'responses', k]))

        # callbacks
        for k, v in six.iteritems(obj.callbacks or {}):
            _resolve(v, CallbackOrReference, self.app, jp_compose([path, 'callbacks', k]))

    @Disp.register([Components])
    def _components(self, path, obj):
        # schemas
        for k, v in six.iteritems(obj.schemas or {}):
            _resolve(v, SchemaOrReference, self.app, jp_compose([path, 'schemas', k]))

        # responses
        for k, v in six.iteritems(obj.responses or {}):
            _resolve(v, ResponseOrReference, self.app, jp_compose([path, 'responses', k]))

        # parameters
        for k, v in six.iteritems(obj.parameters or {}):
            _resolve(v, ParameterOrReference, self.app, jp_compose([path, 'parameters', k]))

        # examples
        for k, v in six.iteritems(obj.examples or {}):
            _resolve(v, ExampleOrReference, self.app, jp_compose([path, 'examples', k]))

        # requestBodies
        for k, v in six.iteritems(obj.request_bodies or {}):
            _resolve(v, RequestBodyOrReference, self.app, jp_compose([path, 'requestBodies', k]))

        # headers
        for k, v in six.iteritems(obj.headers or {}):
            _resolve(v, HeaderOrReference, self.app, jp_compose([path, 'headers', k]))

        # securitySchemes
        for k, v in six.iteritems(obj.security_schemes or {}):
            _resolve(v, SecuritySchemeOrReference, self.app, jp_compose([path, 'securitySchemes', k]))

        # links
        for k, v in six.iteritems(obj.links or {}):
            _resolve(v, LinkOrReference, self.app, jp_compose([path, 'links', k]))

        # callbacks
        for k, v in six.iteritems(obj.callbacks or {}):
            _resolve(v, CallbackOrReference, self.app, jp_compose([path, 'callbacks', k]))

