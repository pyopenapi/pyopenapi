from __future__ import absolute_import
from ...scan import Dispatcher
from ...spec.base2 import list_
from ...spec.v3_0_0.objects import PathItem, Operation, ParameterOrReference
from ...utils import final
from copy import copy


def _merge_parameters(path_item, op):
    if not op:
        return

    if not path_item.parameters:
        return

    final_op = op.final_obj or None
    if not final_op:
        final_op = Operation({})
        final_op.merge_children(op)

    # copy 'parameters' from Operation object
    parameters = list_(ParameterOrReference)([])
    parameters.extend(op.parameters or []) # operation's parameters first
    parameters.extend(path_item.parameters)
    final_op.attach_child('parameters', parameters)

    op.final_obj = final_op


class PatchObject(object):
    """
    - produces/consumes in Operation object should override those in Swagger object.
    - parameters in Operation object should override those in PathItem object.
    - combine parameter list in Operation object from PathItem object
    """

    class Disp(Dispatcher): pass

    def __init__(self, openapi, app):
        self._openapi = openapi
        self._app = app

    @Disp.register([PathItem])
    def _operation(self, path, obj):
        # combine PathItem's parameter to Operation objects
        _merge_parameters(obj, obj.get)
        _merge_parameters(obj, obj.put)
        _merge_parameters(obj, obj.post)
        _merge_parameters(obj, obj.delete)
        _merge_parameters(obj, obj.options)
        _merge_parameters(obj, obj.head)
        _merge_parameters(obj, obj.patch)
        _merge_parameters(obj, obj.trace)

