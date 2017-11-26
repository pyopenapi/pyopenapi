from __future__ import absolute_import
from ...errs import CycleDetectionError
from ...scan import Dispatcher
from ...spec.v3_0_0.objects import PathItem
from ...spec.base import NullContext
from ...utils import CycleGuard


def _merge(obj, path, app, parser):
    """ resolve 'normalized_ref, and inject/merge referenced object to self.
    This operation should be carried in a cascade manner.
    """
    guard = CycleGuard()
    guard.update(obj)

    final = parser({})
    final.merge_children(obj)

    r = obj.normalized_ref
    while r:
        ro = app.resolve(r, parser=parser, spec_version='3.0.0', before_return=None)
        if not ro:
            raise Exception('unable to resolve {} when merging for {}'.format(r, path))

        try:
            guard.update(ro)
        except CycleDetectionError:
            # avoid infinite loop,
            # cycle detection has a dedicated scanner.
            break

        final.merge_children(ro)
        r = ro.normalized_ref

    return final

class Merge(object):
    """ pre-merge these objects with 'normalized_ref' """

    class Disp(Dispatcher): pass

    def __init__(self, app):
        self.app = app

    @Disp.register([PathItem])
    def _path_item(self, path, obj):
        if obj.normalized_ref:
            obj.final_obj = _merge(obj, path, self.app, PathItem)

