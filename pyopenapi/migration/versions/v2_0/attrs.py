# -*- coding: utf-8 -*-

from __future__ import absolute_import
from ...spec.attr import AttributeGroup


class ReferenceAttributeGroup(AttributeGroup):
    __attributes__ = {
        'ref_obj': dict(),
        'normalized_ref': dict(),
    }


class SchemaAttributeGroup(AttributeGroup):
    __attributes__ = {
        'ref_obj': dict(),
        'final': dict(),
        'name': dict(),
        'normalized_ref': dict(),
    }


class PathItemAttributeGroup(AttributeGroup):
    __attributes__ = {
        'ref_obj': dict(),
        'normalized_ref': dict(),
    }
