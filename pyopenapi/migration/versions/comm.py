# -*- coding: utf-8 -*-

from __future__ import absolute_import
from ...errs import CycleDetectionError
from ...utils import CycleGuard


def _merge_path_item(obj, path, from_spec_version, to_spec_version, app, parser,
                     attr_group_cls):
    """ resolve 'normalized_ref, and inject/merge referenced object to self.
    This operation should be carried in a cascade manner.
    """
    guard = CycleGuard()
    guard.update(obj)

    final = parser({})
    final.merge_children(obj)

    attrs = obj.get_attrs('migration', attr_group_cls)
    cur_ref = attrs.normalized_ref
    while cur_ref:
        resolved, _ = app.resolve_obj(
            cur_ref,
            parser=parser,
            from_spec_version=from_spec_version,
            to_spec_version=to_spec_version)
        if not resolved:
            raise Exception('unable to resolve {} when merging for {}'.format(
                cur_ref, path))

        try:
            guard.update(resolved)
        except CycleDetectionError:
            # avoid infinite loop,
            # cycle detection has a dedicated scanner.
            break

        final.merge_children(resolved)

        attrs = resolved.get_attrs('migration', attr_group_cls)
        cur_ref = attrs.normalized_ref

    return final
