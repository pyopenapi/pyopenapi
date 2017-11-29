from __future__ import absolute_import
from ...utils import jp_compose
from ...errs import SchemaError
from ...scan import Dispatcher
from ...spec.v2_0.objects import (
    Operation,
    Schema,
    PathItem,
    Operation,
    Reference,
    ParameterOrReference,
    ResponseOrReference,
    )
import six


def _resolve(o, expected, app, path):
    if not o or not getattr(o, '$ref', None):
        return

    if o.ref_obj:
        return

    if not isinstance(o, (Reference, PathItem, Schema)):
        raise SchemaError('attemp to resolve invalid object: {} in {}'.format(str(type(o)), path))

    if not o.normalized_ref:
        raise ReferenceError('empty normalized_ref for {} in {}'.format(o.ref, path))

    ro = app.resolve(o.normalized_ref, parser=expected, spec_version='2.0', before_return=None)
    if not ro:
        raise ReferenceError('Unable to resolve: {} in {}'.format(o.normalized_ref, path))

    o.ref_obj = ro


class Resolve(object):
    """ pre-resolve 'normalized_ref' """

    class Disp(Dispatcher): pass

    @Disp.register([Schema])
    def _schema(self, path, obj, app):
        _resolve(obj, Schema, app, path)

    @Disp.register([PathItem])
    def _path_item(self, path, obj, app):
        _resolve(obj, PathItem, app, path)

        for idx, s in enumerate(obj.parameters or []):
            _resolve(s, ParameterOrReference, app, jp_compose([path, 'parameters', str(idx)]))

    @Disp.register([Operation])
    def _parameter(self, path, obj, app):
        for idx, s in enumerate(obj.parameters or []):
            _resolve(s, ParameterOrReference, app, jp_compose([path, 'parameters', str(idx)]))

        for k, v in six.iteritems(obj.responses or {}):
            _resolve(v, ResponseOrReference, app, jp_compose([path, 'responses', k]))

