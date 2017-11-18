from ..utils import jr_split
from ..scan import Scanner, Scanner2
from ..scanner.v2_0 import Upgrade
from ..scanner.v3_0_0 import Merge, Resolve, NormalizeRef, PatchObject

def up(obj, app, jref):
    ret = obj
    if ret.__swagger_version__ == '2.0':
        scanner = Scanner(app)
        converter = Upgrade()
        scanner.scan(root=ret, route=[converter])
        ret = converter.openapi
        if not ret:
            raise Exception('unable to upgrade from 2.0: {}'.format(jref))

    if ret.__swagger_version__ == '3.0.0':
        app._cache_spec_obj(ret, *jr_split(jref), spec_version='3.0.0')

        scanner = Scanner2()

        # phase 1: normalized $ref
        url, jp = jr_split(jref)
        scanner.scan(root=ret, route=[NormalizeRef(url)])

        # phase 2: resolve $ref
        scanner.scan(root=ret, route=[Resolve(app)])

        # phase 3: merge path-item
        scanner.scan(root=ret, route=[Merge(app)])

        # phase 4: patch objects
        scanner.scan(root=ret, route=[PatchObject(ret, app)])
    else:
        raise Exception('unsupported migration: {} to 3.0.0'.format(obj.__swagger_version__))

    return ret
