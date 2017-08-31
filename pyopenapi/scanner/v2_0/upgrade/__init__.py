from __future__ import absolute_import
from ....scan import Dispatcher
from ....spec.v2_0.objects import Swagger
from ....spec.v3_0_0.objects import OpenApi
from .converters import to_openapi
import os

class Upgrade(object):
    """ convert 2.0 object to 3.0 object
    """
    class Disp(Dispatcher): pass

    def __init__(self):
        self.openapi = None

    @Disp.register([Swagger])
    def _swagger(self, path, obj, app):
        self.openapi = OpenApi(to_openapi(obj, app, path))
        # TODO: validation ?
