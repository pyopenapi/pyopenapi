# -*- coding: utf-8 -*-

from __future__ import absolute_import
import six

from .....utils import jp_compose
from .....errs import SchemaError, JsonReferenceError
from ....scan import Dispatcher
from ..objects import (
    Operation,
    Schema,
    PathItem,
    Reference,
    ParameterOrReference,
    ResponseOrReference,
)
from ..attrs import (
    ReferenceAttributeGroup,
    PathItemAttributeGroup,
    SchemaAttributeGroup,
)


def _resolve(obj, expected, attr_group_cls, app, path):
    if not obj or not getattr(obj, 'ref', None):
        return

    if not isinstance(obj, (Reference, PathItem, Schema)):
        raise SchemaError('attemp to resolve invalid object: {} in {}'.format(
            str(type(obj)), path))

    attrs = obj.get_attrs('migration', attr_group_cls)
    if attrs.ref_obj:
        return

    if not attrs.normalized_ref:
        raise JsonReferenceError('empty normalized_ref for {} in {}'.format(
            obj.ref, path))

    resolved, _ = app.resolve_obj(
        attrs.normalized_ref,
        from_spec_version='2.0',
        parser=expected,
        remove_dummy=True,
    )
    if not resolved:
        raise JsonReferenceError('Unable to resolve: {} in {}'.format(
            obj.normalized_ref, path))

    attrs.ref_obj = resolved


class Resolve(object):
    """ pre-resolve 'normalized_ref' """

    class Disp(Dispatcher):
        pass

    def __init__(self, app):
        self.app = app

    @Disp.register([Schema])
    def _schema(self, path, obj):
        _resolve(obj, Schema, SchemaAttributeGroup, self.app, path)

    @Disp.register([PathItem])
    def _path_item(self, path, obj):
        _resolve(obj, PathItem, PathItemAttributeGroup, self.app, path)

        for idx, param in enumerate(obj.parameters or []):
            _resolve(param, ParameterOrReference, ReferenceAttributeGroup,
                     self.app, jp_compose([path, 'parameters',
                                           str(idx)]))

    @Disp.register([Operation])
    def _parameter(self, path, obj):
        for idx, param in enumerate(obj.parameters or []):
            _resolve(param, ParameterOrReference, ReferenceAttributeGroup,
                     self.app, jp_compose([path, 'parameters',
                                           str(idx)]))

        for k, resp in six.iteritems(obj.responses or {}):
            _resolve(resp, ResponseOrReference, ReferenceAttributeGroup,
                     self.app, jp_compose([path, 'responses', k]))
