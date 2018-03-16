# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import inspect
import logging

import six

from ..utils import jr_split, jp_split
from .getter import UrlGetter, LocalGetter

logger = logging.getLogger(__name__)


class Resolver(object):
    """ JSON Reference Resolver:
    resolving a JSON reference to a raw object (dict),
    then return and cache it.
    """

    def __init__(self, url_load_hook=None, default_getter=None):
        """
        args:
         - url_load_hook: a way to redirect url to a accessible place, for self testing
         - default_getter: the default getter used when none is provided in 'resolve' method
        """
        # a map from url to loaded json/yaml
        self.__cache = {}

        # things to make unittest easier,
        # all urls to load json would go through this hook
        self.__url_load_hook = url_load_hook

        # default getter for all resolving
        self.__default_getter = default_getter

    def resolve(self, jref, getter=None):
        """
        """
        url, json_pointer = jr_split(jref)

        # apply hook when use this url to load
        # note that we didn't cache App with this local_url
        local_url = self.__url_load_hook(url) if self.__url_load_hook else url

        logger.info('%s patch to %s', url, local_url)

        # check cache
        obj = self.__cache.get(url, None)
        if not obj:
            # load that object
            if not getter:
                getter = self.__default_getter or UrlGetter
                parsed = six.moves.urllib.parse.urlparse(local_url)
                if parsed.scheme == 'file' and parsed.path:
                    getter = LocalGetter(
                        os.path.join(parsed.netloc, parsed.path))

            if inspect.isclass(getter):
                # default initialization is passing the url
                # you can override this behavior by passing an
                # initialized getter object.
                getter = getter(local_url)

            obj = six.advance_iterator(getter)
            self.__cache[url] = obj if obj else None

        if obj:
            parts = jp_split(json_pointer)[1:]
            while parts:
                head = parts.pop(0)
                if isinstance(obj, list):
                    obj = obj[int(head)]
                elif isinstance(obj, dict):
                    obj = obj[head]
                else:
                    raise Exception(
                        'Invalid type to resolve json-pointer: {0}'.format(
                            str(type(obj))))
        else:
            raise Exception('Unable to resolve: {0}'.format(jref))

        return obj


SwaggerResolver = Resolver
