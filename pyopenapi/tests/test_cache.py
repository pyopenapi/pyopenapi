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

