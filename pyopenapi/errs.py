# -*- coding: utf-8 -*-
from __future__ import absolute_import


class CycleDetectionError(Exception):
    pass


class SchemaError(Exception):
    pass


class FieldNotExist(Exception):
    pass


class JsonReferenceError(Exception):
    pass
