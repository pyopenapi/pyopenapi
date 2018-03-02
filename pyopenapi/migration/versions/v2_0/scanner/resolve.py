from __future__ import absolute_import
from ....utils import jp_compose
from ....errs import SchemaError
from ....scan import Dispatcher
from ..objects import (
    Operation,
    Schema,
    PathItem,
    Operation,
    Reference,
    ParameterOrReference,
    ResponseOrReference,
    )
from ..attrs import (
    ReferenceAttributeGroup,
    PathItemAttributeGroup,
    SchemaAttributeGroup,
    )

import six


def _resolve(o, expected, attr_group_cls, app, path):
    if not o or not getattr(o, 'ref', None):
        return

    if not isinstance(o, (Reference, PathItem, Schema)):
        raise SchemaError('attemp to resolve invalid object: {} in {}'.format(str(type(o)), path))

    attrs = o.get_attrs('migration', attr_group_cls)
    if attrs.ref_obj:
        return

    if not attrs.normalized_ref:
        raise ReferenceError('empty normalized_ref for {} in {}'.format(o.ref, path))

    ro, _ = app.resolve_obj(
        attrs.normalized_ref,
        from_spec_version='2.0',
        parser=expected,
        remove_dummy=True,
    )
    if not ro:
        raise ReferenceError('Unable to resolve: {} in {}'.format(o.normalized_ref, path))

    attrs.ref_obj = ro


class Resolve(object):
    """ pre-resolve 'normalized_ref' """

    class Disp(Dispatcher): pass

    def __init__(self, app):
        self.app = app

    @Disp.register([Schema])
    def _schema(self, path, obj):
        _resolve(obj, Schema, SchemaAttributeGroup, self.app, path)

    @Disp.register([PathItem])
    def _path_item(self, path, obj):
        _resolve(obj, PathItem, PathItemAttributeGroup, self.app, path)

        for idx, s in enumerate(obj.parameters or []):
            _resolve(s, ParameterOrReference, ReferenceAttributeGroup, self.app, jp_compose([path, 'parameters', str(idx)]))

    @Disp.register([Operation])
    def _parameter(self, path, obj):
        for idx, s in enumerate(obj.parameters or []):
            _resolve(s, ParameterOrReference, ReferenceAttributeGroup, self.app, jp_compose([path, 'parameters', str(idx)]))

        for k, v in six.iteritems(obj.responses or {}):
            _resolve(v, ResponseOrReference, ReferenceAttributeGroup, self.app, jp_compose([path, 'responses', k]))

