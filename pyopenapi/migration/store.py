from __future__ import absolute_import
from collections import OrderedDict
from distutils.version import StrictVersion  # pylint: disable=no-name-in-module,import-error
from .. import utils, consts
from .spec import _Base
import logging
import six
import os

logger = logging.getLogger(__name__)


class SpecObjStore(object):
    """ cache of spec objects
    """

    def __init__(self, migratable_spec_versions=None):
        self.__spec_objs = {}
        self.__routes = {}
        self.__migratable_spec_versions = False \
            or migratable_spec_versions \
            or utils.get_supported_versions(os.path.join('migration', 'versions'), is_pkg=True)

    #
    # spec object cache
    #

    def set(self, obj, url, jp, spec_version):
        """ cache 'prepared' spec objects (those under pyopenapi.spec)
        """
        if not issubclass(type(obj), _Base):
            raise Exception(
                'attemp to cache invalid object for {},{} with type: {}'.format(
                    url, jp, str(type(obj))))

        self.__spec_objs.setdefault(url, {}).setdefault(jp, {}).update({
            spec_version:
            obj
        })

    def get(self, url, jp, spec_version):
        """ get spec object from cache
        """
        url_cache = self.__spec_objs.get(url, None)
        if not url_cache:
            return None

        # try to find a 'jp' with common prefix with input under 'url'
        for path, cache in six.iteritems(url_cache):
            if jp.startswith(path) and spec_version in cache:
                return cache[spec_version].resolve(
                    utils.jp_split(jp[len(path):])[1:])

        return None

    def get_under(self, url, jp, spec_version, remove=True):
        """ get all children under 'jp', and remove them
        from cache if needed
        """
        if remove and not jp:
            raise Exception(
                'attemping to remove everything under {}, {}'.format(
                    url, spec_version))

        url_cache = self.__spec_objs.get(url, None)
        if not url_cache:
            return None

        ret = {}
        for path, cache in six.iteritems(url_cache):
            if path.startswith(jp) and spec_version in cache:
                ret[path[len(jp) + 1:]] = cache[spec_version]
                if remove:
                    del cache[spec_version]

        return ret

    def get_until(self, url, jp, spec_version, until=None):
        """ get migrated version of one object until 'some' version
        """
        # get relocated 'jp' from older to newer
        jps = [(spec_version, jp)]
        from_ = spec_version
        src = jp
        for v in self.__migratable_spec_versions[
                self.__migratable_spec_versions.index(spec_version) + 1:
                self.__migratable_spec_versions.index(until) + 1
                if until else len(self.__migratable_spec_versions)]:
            src = self.relocate(url, src, from_, to_spec=v)
            from_ = v
            jps.append((v, src))

        # seeking for cached spec objects from newer to older
        for v, j in reversed(jps):
            obj = self.get(url, j, v)
            if obj:
                return obj, j, v

        return None, None, None

    #
    # spec object route
    #

    def update_routes(self, url, to_spec, routes):
        if url not in self.__routes:
            # init the ordered dict with right version sequence
            self.__routes.setdefault(
                url,
                OrderedDict([
                    # there would be no $ref relocation from 1.2 to 2.0,
                    # reason: there is no 'JSON pointer' concept in 1.2
                    (v, {}) for v in self.__migratable_spec_versions
                ]))

        if to_spec not in self.__routes[url]:
            raise Exception(
                'unsupported spec version for $ref-relocation: {}'.format(
                    to_spec))

        self.__routes[url][to_spec].update(routes)

    @staticmethod
    def _patch_jp(jp, routes):
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
                    remain_jp = remain_jp[1:] if remain_jp.startswith(
                        '/') else remain_jp
                    continue
                elif isinstance(patch_to, six.string_types):
                    break
                else:
                    raise Exception(
                        'unexpected JSON pointer patch type: {}:{}'.format(
                            str(type(patch_to)), patch_to))
            else:
                break

        if patch_to:
            remain = jp[len(fixed_prefix + patch_from) + 1:]  # +1 for '/'
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
                new_jp += ('' if new_jp.endswith('/') or remain.startswith('/')
                           else '/') + remain
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

        to_spec = to_spec or consts.DEFAULT_OPENAPI_SPEC_VERSION
        routes = self.__routes[url]

        if to_spec not in routes:
            raise Exception(
                'unsupported target spec version when patching $ref: {}'.format(
                    to_spec))

        from_spec = StrictVersion(from_spec)
        to_spec = StrictVersion(to_spec)
        cur = jp
        for version, r in six.iteritems(routes):
            version = StrictVersion(version)
            if version <= from_spec:
                continue
            if version > to_spec:
                break

            cur = SpecObjStore._patch_jp(cur, r)

        return cur

    @property
    def routes(self):
        return self.__routes
