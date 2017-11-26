from __future__ import absolute_import
from ...errs import CycleDetectionError
from ...scan import Dispatcher
from ...spec.v2_0.parser import (
    SchemaContext,
    PathItemContext,
    ParameterContext,
    ResponseContext,
    )
from ...spec.v2_0.objects import (
    Schema,
    PathItem,
    Parameter,
    Response,
    )

def _resolve(obj, parser, app, path):
    if obj.ref_obj:
        return

    if not obj.normalized_ref:
        return

    ro = app.resolve(
        obj.normalized_ref,
        parser=parser,
        spec_version='2.0',
        before_return=None
    )
    if not ro:
        raise ReferenceError(
            'Unable to resolve: {} in {}'.format(
                obj.normalized_ref, path
            )
        )
    if ro.__class__ != obj.__class__:
        raise TypeError(
            'Referenced Type mismatch: {} in {}'.format(
                obj.normalized_ref, path
            )
        )

    obj.update_field('ref_obj', ro)


class Resolve(object):
    """ pre-resolve 'normalized_ref' """

    class Disp(Dispatcher): pass

    @Disp.register([Schema])
    def _schema(self, path, obj, app):
        _resolve(obj, SchemaContext, app, path)

    @Disp.register([PathItem])
    def _path_item(self, path, obj, app):
        _resolve(obj, PathItemContext, app, path)

    @Disp.register([Parameter])
    def _parameter(self, path, obj, app):
        _resolve(obj, ParameterContext, app, path)

    @Disp.register([Response])
    def _response(self, path, obj, app):
        _resolve(obj, ResponseContext, app, path)

