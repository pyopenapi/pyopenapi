from __future__ import absolute_import
from ...errs import CycleDetectionError
from ...utils import CycleGuard

def _merge_path_item(obj, path, from_spec_version, to_spec_version, app, parser, attr_group_cls):
    """ resolve 'normalized_ref, and inject/merge referenced object to self.
    This operation should be carried in a cascade manner.
    """
    guard = CycleGuard()
    guard.update(obj)

    final = parser({})
    final.merge_children(obj)

    attrs = obj.get_attrs('migration', attr_group_cls)
    r = attrs.normalized_ref
    while r:
        ro, _ = app.resolve_obj(
            r,
            parser=parser,
            from_spec_version=from_spec_version,
            to_spec_version=to_spec_version
        )
        if not ro:
            raise Exception('unable to resolve {} when merging for {}'.format(r, path))

        try:
            guard.update(ro)
        except CycleDetectionError:
            # avoid infinite loop,
            # cycle detection has a dedicated scanner.
            break

        final.merge_children(ro)

        attrs = ro.get_attrs('migration', attr_group_cls)
        r = attrs.normalized_ref

    return final

