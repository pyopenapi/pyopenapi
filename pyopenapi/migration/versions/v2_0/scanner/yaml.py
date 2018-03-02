from __future__ import absolute_import
from ....scan import Dispatcher
from ..objects import (
    Operation,
    MapOfResponseOrReference,
    )
import six


class YamlFixer(object):
    """ fix objects loaded by pyaml """

    class Disp(Dispatcher): pass

    @Disp.register([Operation])
    def _op(self, _, obj):
        """ convert status code in Responses from int to string
        """
        if obj.responses == None: return

        responses = MapOfResponseOrReference({}, obj.responses._path_)
        for k, v in six.iteritems(obj.responses):
            if isinstance(k, six.integer_types):
                responses[str(k)] = v
            else:
                responses[k] = v
        obj.attach_child('responses', responses)

