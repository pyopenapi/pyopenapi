# -*- coding: utf-8 -*-

from ....utils import jr_split
from ...scan import scan
from ..v2_0.scanner.upgrade import converters
from ..v2_0.objects import (
    Swagger,
    Info,
    License,
    Schema,
    PathItem,
)
from .scanner import Resolve, NormalizeRef, Merge
from . import objects


def upgrade(obj, app, jref):
    ret = obj
    reloc = {}
    url, jp = jr_split(jref)
    if ret.__swagger_version__ == '2.0':
        override = None
        if isinstance(ret, (Swagger, License, Info, Schema)):
            override = app.spec_obj_store.get_under(
                url, jp, '3.0.0', remove=False)

        if isinstance(ret, Swagger):
            migrated, reloc = converters.to_openapi(ret, jp)
            ret = objects.OpenApi(migrated, path=jp, override=override)
        elif isinstance(ret, License):
            ret = objects.License(
                converters.to_license(ret, jp), path=jp, override=override)
        elif isinstance(ret, Info):
            ret = objects.Info(
                converters.to_info(ret, jp), path=jp, override=override)
        elif isinstance(ret, Schema):
            ret = objects.Schema(
                converters.to_schema(ret, jp), path=jp, override=override)
        elif isinstance(ret, PathItem):
            migrated, reloc = converters.to_path_item(ret, url, jp)
            ret = objects.PathItem(migrated, path=jp, override=override)
        else:
            raise Exception(
                'unable to upgrade from 2.0: {} for type: {}'.format(
                    jref, str(type(ret))))

    if ret.__swagger_version__ == '3.0.0':
        # phase 1: normalized $ref
        scan(root=ret, route=[NormalizeRef(url)])

        # phase 2: update cache for resolving $ref to current object
        # - because the external document might reference back,
        #   we have to cache ourselves here, just in case.
        app.spec_obj_store.set(ret, url, jp, spec_version='3.0.0')
        app.spec_obj_store.update_routes(url, '3.0.0', {jp: reloc})

        # phase 3: resolve $ref
        scan(root=ret, route=[Resolve(app)])

        # phase 4: merge path item from $ref
        scan(root=ret, route=[Merge(app)])
    else:
        raise Exception('unsupported migration: {} to 3.0.0'.format(
            obj.__swagger_version__))

    return ret, reloc
