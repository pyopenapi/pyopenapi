# -*- coding: utf-8 -*-

from __future__ import absolute_import
from ....scan import Dispatcher
from ...comm import _merge_path_item
from ..objects import PathItem
from ..attrs import PathItemAttributeGroup


class Merge(object):
    """ pre-merge these objects with 'normalized_ref' """

    class Disp(Dispatcher):
        pass

    def __init__(self, app):
        self.app = app

    @Disp.register([PathItem])
    def _path_item(self, path, obj):
        if obj.ref:
            obj.get_attrs('migration',
                          PathItemAttributeGroup).final_obj = _merge_path_item(
                              obj, path, '2.0', '2.0', self.app, PathItem,
                              PathItemAttributeGroup)
