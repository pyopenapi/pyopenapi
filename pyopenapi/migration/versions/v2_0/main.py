# -*- coding: utf-8 -*-

from __future__ import absolute_import
from ....utils import jr_split
from ...scan import scan
from ..v1_2.scanner import Upgrade
from .scanner import Resolve, YamlFixer, NormalizeRef, Merge
from .objects import Operation


def upgrade(obj, app, jref):
    ret = obj

    if ret.__swagger_version__ == '1.2':
        converter = Upgrade(sep=app.sep)

        scan(root=ret, route=[converter])
        # scan through each resource
        for name in ret.cached_apis:
            scan(root=ret.cached_apis[name], route=[converter])

        ret = converter.get_swagger()
        if not ret:
            raise Exception('unable to upgrade from 1.2: {}'.format(jref))

    if ret.__swagger_version__ == '2.0':
        url, jp = jr_split(jref)
        app.spec_obj_store.set(ret, url, jp, spec_version='2.0')

        # normalize $ref
        scan(root=ret, route=[NormalizeRef(url)])
        # fix for yaml that treat response code as number
        scan(root=ret, route=[YamlFixer()], leaves=[Operation])

        # cache this object before resolving external(possible) object
        app.spec_obj_store.set(ret, url, jp, spec_version='2.0')

        # pre resolve Schema Object
        # note: make sure this object is cached before using 'Resolve' scanner
        scan(root=ret, route=[Resolve(app)])

        # merge path-item
        scan(root=ret, route=[Merge(app)])
    else:
        raise Exception('unsupported migration: {} to 2.0'.format(
            ret.__swagger_version__))

    return ret, {}
