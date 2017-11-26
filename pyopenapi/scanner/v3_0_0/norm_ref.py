from __future__ import absolute_import
from ...scan import Dispatcher
from ...utils import normalize_jr
from ...spec.v3_0_0.objects import PathItem, Reference


class NormalizeRef(object):
    """ normalized all $ref """

    class Disp(Dispatcher): pass

    def __init__(self, base_url):
        self.base_url = base_url

    @Disp.register([Reference, PathItem])
    def _reference(self, path, obj):
        if obj.ref:
            obj.normalized_ref = normalize_jr(obj.ref, self.base_url)

