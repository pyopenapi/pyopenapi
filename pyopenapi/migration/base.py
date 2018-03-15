# -*- coding: utf-8 -*-

from __future__ import absolute_import

import abc
import logging
import pkgutil
import weakref
import os
from distutils.version import StrictVersion  # pylint: disable=no-name-in-module,import-error

import six
from .. import utils, consts
from .resolve import Resolver
from .store import SpecObjStore
from .versions.v1_2.objects import ResourceListing, ApiDeclaration
from .versions.v2_0.objects import Swagger
from .versions.v3_0_0.objects import OpenApi

logger = logging.getLogger(__name__)


class ApiBase(six.with_metaclass(abc.ABCMeta, object)):
    """
    """

    def __init__(self,
                 url=None,
                 url_load_hook=None,
                 resolver=None,
                 sep=consts.SCOPE_SEPARATOR):
        """ constructor

        :param url str: url of swagger.json
        :param func url_load_hook: a way to redirect url to a accessible place. for self testing.
        :param resolver: pyopenapi.resolve.Resolver: customized resolver used as default when none is provided when resolving
        :param sep str: separator used by pyopenapi.migration.utils.ScopeDict
        """

        self.__original_spec_version = ''
        self.__url = url

        # migratable spec version
        self.__migratable_spec_versions = utils.get_supported_versions(
            os.path.join('migration', 'versions'), is_pkg=True)

        # init property for 'current loaded spec version'
        # when the loaded object is a root one.
        self.__current_spec_version = None

        # a map from json-reference to
        # - spec.base2._Base
        # - a map from json-pointer to spec.base2._Base
        #
        # and a map from json-reference in older OpenApi spec
        # to json-reference in migrated OpenApi spec
        self.__store = SpecObjStore(
            migratable_spec_versions=self.migratable_spec_versions)

        if url_load_hook and resolver:
            raise ValueError(
                'when use customized Resolver, please pass url_load_hook to that one'
            )

        # the start-point when you want to traverse the code to laod new object
        self.__resolver = resolver or Resolver(url_load_hook)

        # allow init App-wised SCOPE_SEPARATOR
        self.__sep = sep

    @property
    def sep(self):
        """ separator used by pyswager.utils.ScopeDict
        """
        return self.__sep

    @property
    def original_spec_version(self):
        """ original spec version of loaded json

        :type: str
        """
        return self.__original_spec_version

    @property
    def current_spec_version(self):
        """ to which OpenApi spec version
        the loaded spec migrated to

        :type: str
        """
        return self.__current_spec_version

    @property
    def migratable_spec_versions(self):
        """ list of migratable spec version, ex.
        ['2.0', '3.0.0']
        """
        return self.__migratable_spec_versions

    @property
    def url(self):
        """
        """
        return self.__url

    @property
    def resolver(self):
        """ JSON Reference resolver

        :type: pyopenapi.resolve.Resolver
        """
        return self.__resolver

    @property
    def spec_obj_store(self):
        """ Storefor Spec Objects

        :type: pyopenapi.cache.SpecObjStore
        """
        return self.__store

    def load_obj(self, jref, getter=None, parser=None, remove_dummy=False):
        """ load a object(those in spec._version_.objects) from a JSON reference.
        """
        src_spec = self.__resolver.resolve(jref, getter)

        # get root document to check its swagger version.
        obj = None
        version = utils.get_swagger_version(src_spec)
        url, jp = utils.jr_split(jref)

        # usually speaking, we would only enter App.load_obj when App.resolve
        # can't find the object. However, the 'version' in App.load_obj might
        # be different from the one passed into App.resolve.
        #
        # Therefore, we need to check the cache here again.
        obj = self.spec_obj_store.get(url, jp, version)
        if obj:
            return obj

        override = self.spec_obj_store.get_under(
            url, jp, version, remove=remove_dummy)
        if version == '1.2':
            obj = ResourceListing(src_spec, jref, {})

            resources = []
            for resource in obj.apis:  # pylint: disable=no-member
                resources.append(resource.path)

            base = utils.url_dirname(jref)
            urls = zip(
                map(lambda u: utils.url_join(base, u[1:]), resources),
                map(lambda u: u[1:], resources))

            cached_apis = {}
            for url, name in urls:
                resource_spec = self.resolver.resolve(url, getter)
                if resource_spec is None:
                    raise Exception(
                        'unable to resolve {} when load spec from {}'.format(
                            url, jref))
                cached_apis[name] = ApiDeclaration(resource_spec,
                                                   utils.jp_compose(
                                                       name, base=url), {})

            obj.cached_apis = cached_apis

        # after Swagger 2.0, we need to handle
        # the loading order of external reference

        elif version == '2.0':
            # swagger 2.0
            obj = Swagger(src_spec, jref, override)

        elif version == '3.0.0':
            # openapi 3.0.0
            obj = OpenApi(src_spec, jref, override)

        elif version is None and parser:
            obj = parser(src_spec, jref, {})
            version = obj.__swagger_version__ if hasattr(
                obj, '__swagger_version__') else version
        else:
            raise NotImplementedError(
                'Unsupported Swagger Version: {0} from {1}'.format(
                    version, jref))

        if not obj:
            raise Exception('Unable to parse object from {0}'.format(jref))

        logger.info('version: %s', version)

        # cache obj before migration, or we may load an object multiple times when resolve
        # $ref in the same spec
        self.spec_obj_store.set(obj, url, jp, spec_version=version)

        if isinstance(obj, (OpenApi, Swagger, ResourceListing)):
            self.__original_spec_version = obj.__swagger_version__

        return obj

    def migrate_obj(self, obj, jref, spec_version):
        """ migrate an object(those in spec._version_.objects)
        """
        spec_version = spec_version
        supported_versions = self.migratable_spec_versions

        if spec_version not in supported_versions:
            raise ValueError(
                'unsupported spec version: {}'.format(spec_version))

        # only keep required version strings for this migration
        supported_versions = supported_versions[:(
            supported_versions.index(spec_version) + 1)]

        # filter out those migration with lower version than current one
        supported_versions = [
            v for v in supported_versions
            if StrictVersion(obj.__swagger_version__) <= StrictVersion(v)
        ]

        # load migration module
        url, relocated_jp = utils.jr_split(jref)
        from_spec_version = obj.__swagger_version__
        for version in supported_versions:
            patched_version = 'v{}'.format(version).replace('.', '_')
            migration_module_path = '.'.join(
                ['pyopenapi', 'migration', 'versions', patched_version, 'main'])
            loader = pkgutil.find_loader(migration_module_path)
            if not loader:
                raise Exception('unable to find module loader for {}'.format(
                    migration_module_path))

            migration_module = loader.load_module(migration_module_path)
            if not migration_module:
                raise Exception('unable to load {} for migration'.format(
                    migration_module_path))

            # preform migration
            obj, reloc = migration_module.upgrade(obj, self, jref)

            # update route for object relocation
            self.spec_obj_store.update_routes(url, version,
                                              {relocated_jp: reloc})

            # update JSON pointer for next round
            relocated_jp = self.spec_obj_store.relocate(
                url, relocated_jp, from_spec_version, version)

            # prepare this object if needy
            obj = self.prepare_obj(obj, url + relocated_jp)

            # cache migrated and prepared object if we need it later
            self.spec_obj_store.set(
                obj, url, relocated_jp, spec_version=version)

            from_spec_version = version

        if isinstance(obj, (OpenApi, Swagger, ResourceListing)):
            self.__current_spec_version = spec_version

        return obj

    def resolve_obj(self,
                    jref,
                    from_spec_version,
                    parser=None,
                    to_spec_version=None,
                    remove_dummy=False):
        """ internal JSON reference resolver

        :param str jref: a JSON Reference, refer to http://tools.ietf.org/html/draft-pbryan-zyp-json-ref-03 for details.
        :param str from_spec_version: the spec version of Api document where 'jref' is used
        :param parser: the parser corresponding to target object.
        :param str to_spec_version: the expected spec version of resolved object
        :param str from_spec_version: the OpenAPI spec version 'jref' pointing to.
        :param bool remove_dummy: a flag to tell pyopenapi to clean dummy objects in pyopenapi.spec_obj_store
        :type parser: pyopenapi.base.Context
        :return: the referenced object, wrapped by weakref.ProxyType
        :rtype: weakref.ProxyType
        :raises ValueError: if path is not valid
        """

        logger.info('resolving: [%s]', jref)

        if not jref:
            raise ValueError('Empty Path is not allowed')

        to_spec_version = to_spec_version or from_spec_version

        # migrate $ref
        url, jp = utils.jr_split(jref)
        if not url:
            # assume it targets the root document
            url = self.url
            jref = url + jp

        relocated_jp = jp
        if from_spec_version != to_spec_version:
            relocated_jp = self.spec_obj_store.relocate(
                url, jp, from_spec_version, to_spec_version)

        # check cacahed object against json reference by
        # comparing url first, and find those object prefixed with
        # the JSON pointer.
        obj = self.spec_obj_store.get(url, relocated_jp, to_spec_version)

        # this object is not found in cache
        if obj is None:
            # attempt to load object via input JSON pointer
            obj, j, _ = self.spec_obj_store.get_until(
                url, jp, from_spec_version, until=to_spec_version)
            if obj is None:
                if from_spec_version != self.original_spec_version:
                    raise Exception(
                        'object is not loadable, you need to provide JSON pointer from source spec version:{}, not {}'.
                        format(self.original_spec_version, from_spec_version))
                obj = self.load_obj(
                    jref, parser=parser, remove_dummy=remove_dummy)
            else:
                jref = url + j

            obj = obj and self.migrate_obj(obj, jref, to_spec_version)
            obj = obj and self.prepare_obj(obj, jref)

            relocated_jp = self.spec_obj_store.relocate(
                url, jp, from_spec_version, to_spec_version)

        if obj is None:
            raise ValueError('Unable to resolve path, [{0}]'.format(jref))

        if isinstance(obj, (six.string_types, six.integer_types, list, dict)):
            return obj, relocated_jp

        return weakref.proxy(obj), url + relocated_jp

    @abc.abstractmethod
    def prepare_obj(self, obj, jref):
        return obj
