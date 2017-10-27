from ..scan import Scanner
from ..scanner.v2_0 import Upgrade

def up(obj, app, jref):
    ret = obj
    scanner = Scanner(app)
    if ret.__swagger_version__ == '2.0':
        converter = Upgrade()
        scanner.scan(root=ret, route=[converter])
        ret = converter.openapi
        if not ret:
            raise Exception('unable to upgrade from 2.0: {}'.format(jref))
    else:
        raise Exception('unsupported migration: {} to 3.0.0'.format(obj.__swagger_version__))

    return ret
