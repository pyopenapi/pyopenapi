from pyopenapi.cache import SpecObjCache
from pyopenapi.spec.v2_0.objects import Swagger, Info
from pyopenapi.spec.v3_0_0.objects import OpenApi
from .utils import get_test_file
import unittest
import json


class SpecObjCacheTestCase(unittest.TestCase):
    """ test case for SpecObjCache """

    def test_get_and_set_for_same_version(self):
        """ get and set for the same version
        """

        cache = SpecObjCache()

        url = 'http://localhost'
        jp = '#'
        version = '2.0'
        obj = Swagger(json.loads(get_test_file(
            version, 'wordnik', 'swagger.json'
        )), '#', {})

        cache.set(obj, url, jp, version)
        self.assertEqual(id(obj), id(cache.get(url, jp, version)))

        # get a child
        self.assertTrue(isinstance(cache.get(url, '#/info', version), Info))

        # get different version
        self.assertEqual(None, cache.get(url, '#', '3.0.0'))

        # another cache with Info object
        cache2 = SpecObjCache()
        cache2.set(cache.get(url, '#/info', version), url, '#/info', version)

        # attemp to get its parent -> Swagger
        self.assertEqual(None, cache2.get(url, '#', version))

    def test_get_under(self):
        """ check if 'get_under' works
        """
        cache = SpecObjCache()

        url = 'http://localhost'
        jp = '#'
        version = '2.0'
        obj = Swagger(json.loads(get_test_file(
            version, 'wordnik', 'swagger.json'
        )), '#', {})

        cache.set(obj, url, jp, version)
        cache.set(obj.info, url, '#/info', version)
        cache.set(obj.info.license, url, '#/info/license', version)
        cache.set(obj.definitions['Order'], url, '#/definitions/Order', version)
        cache.set(obj.definitions['Order'].properties['id'], url, '#/definitions/Order/properties/id', version)
        cache.set(obj.definitions['Pet'], url, '#/definitions/Pet', version)

        under = cache.get_under(url, '#', version, remove=False)
        self.assertEqual(sorted(under.keys()), sorted([
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
        self.assertEqual(id(obj.definitions['Order']), id(under['definitions/Order']))
        self.assertEqual(id(obj.definitions['Order'].properties['id']), id(under['definitions/Order/properties/id']))
        self.assertEqual(id(obj.definitions['Pet']), id(under['definitions/Pet']))

        under = cache.get_under(url, '#/info', version)
        self.assertEqual(sorted(under.keys()), sorted(['', 'license']))
        self.assertEqual({}, cache.get_under(url, '#/info', version))

        # test remove
        under = cache.get_under(url, '#/definitions/Order', version)
        self.assertEqual(sorted(under.keys()), sorted(['', 'properties/id']))
        self.assertEqual({}, cache.get_under(url, '#/definitions/Order', version))

        under = cache.get_under(url, '#/definitions', version)
        self.assertEqual(under.keys(), ['Pet'])
        self.assertEqual({}, cache.get_under(url, '#/definitions', version))

        under = cache.get_under(url, '#', version)
        self.assertEqual(under.keys(), [''])
        self.assertEqual({}, cache.get_under(url, '#', version))

        # get with empty string is not allowed
        self.assertRaises(Exception, cache.get_under, url, '', version)

