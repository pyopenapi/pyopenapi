from __future__ import absolute_import
from ...errs import CycleDetectionError
from ...scan import Dispatcher
from ...spec.v2_0.parser import SchemaContext
from ...spec.v2_0.objects import Schema

class Resolve(object):
    """ pre-resolve 'normalized_ref' """

    class Disp(Dispatcher): pass

    @Disp.register([Schema])
    def _schema(self, _, obj, app):
        if obj.ref_obj:
            return

        r = obj.normalized_ref
        if not r:
            return

        ro = app.resolve(r, parser=SchemaContext, spec_version='2.0', before_return=None)
        if not ro:
            raise ReferenceError('Unable to resolve: {0}'.format(r))
        if ro.__class__ != obj.__class__:
            raise TypeError('Referenced Type mismatch: {0}'.format(r))

        obj.update_field('ref_obj', ro)


