# -*- coding: utf-8 -*-

from __future__ import absolute_import
import six

from ....scan import Dispatcher
from ..objects import (
    Operation,
    MapOfResponseOrReference,
)


class YamlFixer(object):
    """ fix objects loaded by pyaml """

    class Disp(Dispatcher):
        pass

    # pylint: disable=no-self-use
    @Disp.register([Operation])
    def _op(self, _, obj):
        """ convert status code in Responses from int to string
        """
        if obj.responses is None:
            return

        responses = MapOfResponseOrReference({}, obj.responses.get_path())
        for k, resp in six.iteritems(obj.responses):
            if isinstance(k, six.integer_types):
                responses[str(k)] = resp
            else:
                responses[k] = resp
        obj.attach_child('responses', responses)
