from pyopenapi.migration.store import SpecObjStore
from pyopenapi.migration.versions.v2_0.objects import Swagger, Info
from pyopenapi.migration.versions.v3_0_0.objects import OpenApi
from ..utils import get_test_file
import unittest
import json


class SpecObjStoreTestCase(unittest.TestCase):
    """ test case for SpecObjCache """

    def test_cache_get_and_set_for_same_version(self):
        """ get and set for the same version
        """

        cache = SpecObjStore()

        url = 'http://localhost'
        jp = '#'
        version = '2.0'
        obj = Swagger(
            json.loads(get_test_file(version, 'wordnik', 'swagger.json')), '#',
            {})

        cache.set(obj, url, jp, version)
        self.assertEqual(id(obj), id(cache.get(url, jp, version)))

        # get a child
        self.assertTrue(isinstance(cache.get(url, '#/info', version), Info))

        # get different version
        self.assertEqual(None, cache.get(url, '#', '3.0.0'))

        # another cache with Info object
        cache2 = SpecObjStore()
        cache2.set(cache.get(url, '#/info', version), url, '#/info', version)

        # attemp to get its parent -> Swagger
        self.assertEqual(None, cache2.get(url, '#', version))

    def test_cache_get_under(self):
        """ check if 'get_under' works
        """
        cache = SpecObjStore()

        url = 'http://localhost'
        jp = '#'
        version = '2.0'
        obj = Swagger(
            json.loads(get_test_file(version, 'wordnik', 'swagger.json')), '#',
            {})

        cache.set(obj, url, jp, version)
        cache.set(obj.info, url, '#/info', version)
        cache.set(obj.info.license, url, '#/info/license', version)
        cache.set(obj.definitions['Order'], url, '#/definitions/Order', version)
        cache.set(obj.definitions['Order'].properties['id'], url,
                  '#/definitions/Order/properties/id', version)
        cache.set(obj.definitions['Pet'], url, '#/definitions/Pet', version)

        under = cache.get_under(url, '#', version, remove=False)
        self.assertEqual(
            sorted(under.keys()),
            sorted([
                '',
                'definitions/Order',
                'definitions/Order/properties/id',
                'definitions/Pet',
                'info',
                'info/license',
            ]))
        self.assertEqual(id(obj), id(under['']))
        self.assertEqual(id(obj.info), id(under['info']))
        self.assertEqual(id(obj.info.license), id(under['info/license']))
        self.assertEqual(
            id(obj.definitions['Order']), id(under['definitions/Order']))
        self.assertEqual(
            id(obj.definitions['Order'].properties['id']),
            id(under['definitions/Order/properties/id']))
        self.assertEqual(
            id(obj.definitions['Pet']), id(under['definitions/Pet']))

        under = cache.get_under(url, '#/info', version)
        self.assertEqual(sorted(under.keys()), sorted(['', 'license']))
        self.assertEqual({}, cache.get_under(url, '#/info', version))

        # test remove
        under = cache.get_under(url, '#/definitions/Order', version)
        self.assertEqual(sorted(under.keys()), sorted(['', 'properties/id']))
        self.assertEqual({}, cache.get_under(url, '#/definitions/Order',
                                             version))

        under = cache.get_under(url, '#/definitions', version)
        self.assertEqual(list(under.keys()), ['Pet'])
        self.assertEqual({}, cache.get_under(url, '#/definitions', version))

        under = cache.get_under(url, '#', version)
        self.assertEqual(list(under.keys()), [''])
        self.assertEqual({}, cache.get_under(url, '#', version))

        # get with empty string is not allowed
        self.assertRaises(Exception, cache.get_under, url, '', version)

    def test_cache_get_until(self):
        """ make sure we could get latest object
        """

        url = 'http://localhost'
        cache = SpecObjStore(
            migratable_spec_versions=['2.0', '3.0', '4.0', '5.0', '6.0'])

        cache.update_routes(url, '3.0', {'#': '#/a'})
        cache.update_routes(url, '4.0', {'#/a': '#/b'})
        cache.update_routes(url, '5.0', {'#/b': '#/c'})

        # only '2.0' is available
        obj_2_0 = Swagger({})
        cache.set(obj_2_0, url, '#', '2.0')
        obj, j, v = cache.get_until(url, '#', '2.0')
        self.assertEqual(id(obj), id(obj_2_0))
        self.assertEqual(j, '#')
        self.assertEqual(v, '2.0')

        # '3.0' is available now
        obj_3_0 = Swagger({})
        cache.set(obj_3_0, url, '#/a', '3.0')
        obj, j, v = cache.get_until(url, '#', '2.0')
        self.assertEqual(id(obj), id(obj_3_0))
        self.assertEqual(j, '#/a')
        self.assertEqual(v, '3.0')

        # '4.0' is available now
        obj_4_0 = Swagger({})
        cache.set(obj_4_0, url, '#/b', '4.0')
        obj, j, v = cache.get_until(url, '#', '2.0')
        self.assertEqual(id(obj), id(obj_4_0))
        self.assertEqual(j, '#/b')
        self.assertEqual(v, '4.0')

        # '5.0' is available now
        obj_5_0 = Swagger({})
        cache.set(obj_5_0, url, '#/c', '5.0')
        obj, j, v = cache.get_until(url, '#', '2.0')
        self.assertEqual(id(obj), id(obj_5_0))
        self.assertEqual(j, '#/c')
        self.assertEqual(v, '5.0')

        # until 2.0
        obj, j, v = cache.get_until(url, '#', '2.0', until='2.0')
        self.assertEqual(id(obj), id(obj_2_0))
        self.assertEqual(j, '#')
        self.assertEqual(v, '2.0')
        # until 3.0
        obj, j, v = cache.get_until(url, '#', '2.0', until='3.0')
        self.assertEqual(id(obj), id(obj_3_0))
        self.assertEqual(j, '#/a')
        self.assertEqual(v, '3.0')
        # until 4.0
        obj, j, v = cache.get_until(url, '#', '2.0', until='4.0')
        self.assertEqual(id(obj), id(obj_4_0))
        self.assertEqual(j, '#/b')
        self.assertEqual(v, '4.0')
        # until 5.0
        obj, j, v = cache.get_until(url, '#', '2.0', until='5.0')
        self.assertEqual(id(obj), id(obj_5_0))
        self.assertEqual(j, '#/c')
        self.assertEqual(v, '5.0')
        # until 6.0
        obj, j, v = cache.get_until(url, '#', '2.0', until='6.0')
        self.assertEqual(id(obj), id(obj_5_0))
        self.assertEqual(j, '#/c')
        self.assertEqual(v, '5.0')

    def test_route_invalid_version(self):
        """ make sure only supported version could
        be used
        """
        url = 'http://localhost/some/path'
        rm = SpecObjStore()
        self.assertRaises(Exception, rm.update_routes, url, '1.1', {})

        # 'to' version not in route
        self.assertRaises(Exception, rm.relocate, url, '#/some/jp', '2.0',
                          '2.1')

    def test_route_empty_route(self):
        """ empty route should return original JSON pointer
        """
        url = 'http://localhost/some/path'
        rm = SpecObjStore()

        rm.update_routes(url, '3.0.0', {})
        self.assertEqual(
            rm.relocate(url, '#/some/jp', '1.2', '3.0.0'), '#/some/jp')

    def test_route_fake_route(self):
        """ make sure patching with route from
        older spec to newer spec works
        """
        url = 'http://localhost/some/path'
        rm = SpecObjStore()

        rm.update_routes(url, '3.0.0', {})
        self.assertEqual(
            rm.relocate(url, '#/some/json/pointer', '1.2', '3.0.0'),
            '#/some/json/pointer')

        # the result of multiple calls to 'update' could be accumulated
        rm.update_routes(url, '3.0.0', {'#/some': '#/some3'})
        self.assertEqual(
            rm.relocate(url, '#/some/json/pointer', '1.2', '3.0.0'),
            '#/some3/json/pointer')

        # longer JSON pointer would be picked
        rm.update_routes(url, '3.0.0', {'#/some/json': '#/some3/json3'})
        self.assertEqual(
            rm.relocate(url, '#/some/json/pointer', '1.2', '3.0.0'),
            '#/some3/json3/pointer')

    def test_route_nested_route(self):
        """ make sure nested route works
        """
        url = 'http://localhost/some/path'
        rm = SpecObjStore()

        rm.update_routes(
            url,
            '3.0.0',
            {
                '#': {
                    'some/path': {
        # relative, just replace the last part
                        'to/another/one': 'another2/two'
                    },

        # real example from 3.0.0
                    'parameters': {
                        '': '#/components/parameters',
                        'body_1': '#/components/requestBodies/body_1'
                    },
                    'paths': {
                        '~1p3': {
                            'parameters/3': 'x-pyopenapi_internal_request_body'
                        }
                    }
                }
            })

        self.assertEqual(
            rm.relocate(url, '#/some/path/to/another/one/test', '2.0', '3.0.0'),
            '#/some/path/another2/two/test')
        self.assertEqual(
            rm.relocate(url, '#/parameters', '2.0', '3.0.0'),
            '#/components/parameters')
        self.assertEqual(
            rm.relocate(url, '#/parameters/body_1', '2.0', '3.0.0'),
            '#/components/requestBodies/body_1')
        self.assertEqual(
            rm.relocate(url, '#/paths/~1p3/parameters/3', '2.0', '3.0.0'),
            '#/paths/~1p3/x-pyopenapi_internal_request_body')
