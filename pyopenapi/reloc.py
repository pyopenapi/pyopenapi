from __future__ import absolute_import
from .consts import private
from .utils import get_supported_versions
from collections import OrderedDict
from distutils.version import StrictVersion
import logging
import six


logger = logging.getLogger(__name__)


class SpecObjReloc(object):
    """ map of $ref to guide the patching when migrating specs
    """

    def __init__(self):
        self.__routes = {}

    def update(self, url, to_spec, routes):
        if url not in self.__routes:
            # init the ordered dict with right version sequence
            self.__routes.setdefault(url, OrderedDict([
                # there would be no $ref relocation from 1.2 to 2.0,
                # reason: there is no 'JSON pointer' concept in 1.2
                (v, {}) for v in get_supported_versions('migration', is_pkg=False)
            ]))

        if to_spec not in self.__routes[url]:
            raise Exception('unsupported spec version for $ref-relocation: {}'.format(to_spec))

        self.__routes[url][to_spec].update(routes)

    @staticmethod
    def patch(jp, routes):
        current_routes = routes
        fixed_prefix = ''
        patch_to = None
        remain_jp = jp
        while True:
            patch_from = None
            for f, t in six.iteritems(current_routes):
                # find the longest prefix in f(rom)
                if not remain_jp.startswith(f):
                    continue
                if not patch_from or len(f) > len(patch_from):
                    patch_from, patch_to = f, t

            if patch_to:
                if isinstance(patch_to, dict):
                    # nested route map
                    current_routes, patch_to = patch_to, None
                    fixed_prefix += ('/' if fixed_prefix else '') + patch_from
                    remain_jp = remain_jp[len(patch_from):]
                    remain_jp = remain_jp[1:] if remain_jp.startswith('/') else remain_jp
                    continue
                elif isinstance(patch_to, six.string_types):
                    break
                else:
                    raise Exception(
                        'unexpected JSON pointer patch type: {}:{}'.format(
                            str(type(patch_to)), patch_to
                        )
                    )
            else:
                break

        if patch_to:
            remain = jp[len(fixed_prefix + patch_from)+1:] # +1 for '/'
            new_jp = None
            # let's patch the JSON pointer
            if patch_to.startswith('#'):
                # an absolute JSON point
                new_jp = patch_to
            else:
                # a relavie path case, need to compose
                # a qualified JSON pointer
                new_jp = fixed_prefix + '/' + patch_to

            if remain:
                new_jp += ('' if new_jp.endswith('/') or remain.startswith('/') else '/') + remain
            return new_jp

        # there is no need for relocation
        return jp

    def relocate(self, url, jp, from_spec, to_spec=None):
        """ $ref relocation

        :param url str: url part of JSON reference
        :param jp str: JSON pointer part of JSON reference
        :param from_spec str: the spec version that 'url' and 'jp' exits
        :param to_spec str: the target spec version you want to patch 'jp'

        :return str: return the 'relocated' JSON pointer
        """
        if url not in self.__routes:
            return jp

        to_spec = to_spec or private.DEFAULT_OPENAPI_SPEC_VERSION
        routes = self.__routes[url]

        if to_spec not in routes:
            raise Exception('unsupported target spec version when patching $ref: {}'.format(to_spec))

        from_spec = StrictVersion(from_spec)
        to_spec = StrictVersion(to_spec)
        cur = jp
        for version, r in six.iteritems(routes):
            version = StrictVersion(version)
            if version <= from_spec:
                continue
            if version > to_spec:
                break

            cur = SpecObjReloc.patch(cur, r)

        return cur

    @property
    def routes(self):
        return self.__routes
