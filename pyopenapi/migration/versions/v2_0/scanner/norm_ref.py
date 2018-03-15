# -*- coding: utf-8 -*-

from __future__ import absolute_import
from .....utils import normalize_jr
from ....scan import Dispatcher
from ..objects import (
    Schema,
    PathItem,
    Reference,
)
from ..attrs import (
    SchemaAttributeGroup,
    ReferenceAttributeGroup,
    PathItemAttributeGroup,
)


def _normalize(obj, base_url, attr_group_cls):
    if obj.ref:
        attrs = obj.get_attrs('migration', attr_group_cls)
        attrs.normalized_ref = normalize_jr(obj.ref, base_url)


class NormalizeRef(object):
    """ normalized all $ref """

    class Disp(Dispatcher):
        pass

    def __init__(self, base_url):
        self.base_url = base_url

    @Disp.register([Schema])
    def _schema(self, _, obj):
        _normalize(obj, self.base_url, SchemaAttributeGroup)

    @Disp.register([Reference])
    def _reference(self, _, obj):
        _normalize(obj, self.base_url, ReferenceAttributeGroup)

    @Disp.register([PathItem])
    def _path_item(self, _, obj):
        _normalize(obj, self.base_url, PathItemAttributeGroup)
