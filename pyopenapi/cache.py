from __future__ import absolute_import
from .spec.base2 import _Base
from . import utils
import logging
import six


logger = logging.getLogger(__name__)


class SpecObjCache(object):
    """ cache of prepared objects
    """

    def __init__(self):
        self.__spec_objs = {}

    def set(self, obj, url, jp, spec_version):
        """ cache 'prepared' spec objects (those under pyopenapi.spec)
        """
        if not issubclass(type(obj), _Base):
            raise Exception('attemp to cache invalid object for {},{} with type: {}'.format(url, jp, str(type(obj))))

        self.__spec_objs.setdefault(url, {}).setdefault(jp, {}).update({spec_version: obj})

    def get(self, url, jp, spec_version):
        """ get spec object from cache
        """
        url_cache = self.__spec_objs.get(url, None)
        if not url_cache:
            return None

        # try to find a 'jp' with common prefix with input under 'url'
        for path, cache in six.iteritems(url_cache):
            if jp.startswith(path) and spec_version in cache:
                return cache[spec_version].resolve(utils.jp_split(jp[len(path):])[1:])

        return None
