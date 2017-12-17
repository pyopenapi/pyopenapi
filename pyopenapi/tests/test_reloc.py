from pyopenapi.reloc import SpecObjReloc
import unittest


class SpecObjRelocTestCase(unittest.TestCase):
    """ test case for SpecObjReloc """

    def test_invalid_version(self):
        """ make sure only supported version could
        be used
        """
        url = 'http://localhost/some/path'
        rm = SpecObjReloc()
        self.assertRaises(Exception, rm.update, url, '1.1', {})

        # 1.2 should not be included
        self.assertRaises(Exception, rm.update, url, '1.2', {})

        # 'to' version not in route
        self.assertRaises(Exception, rm.relocate, url, '#/some/jp', '2.0', '2.1')

    def test_empty_route(self):
        """ empty route should return original JSON pointer
        """
        url = 'http://localhost/some/path'
        rm = SpecObjReloc()

        rm.update(url, '3.0.0', {})
        self.assertEqual(rm.relocate(url, '#/some/jp', '1.2', '3.0.0'), '#/some/jp')

    def test_with_fake_route(self):
        """ make sure patching with route from
        older spec to newer spec works
        """
        url = 'http://localhost/some/path'
        rm = SpecObjReloc()

        rm.update(url, '3.0.0', {})
        self.assertEqual(
            rm.relocate(url, '#/some/json/pointer', '1.2', '3.0.0'),
            '#/some/json/pointer'
        )

        # the result of multiple calls to 'update' could be accumulated
        rm.update(url, '3.0.0', {'#/some': '#/some3'})
        self.assertEqual(
            rm.relocate(url, '#/some/json/pointer', '1.2', '3.0.0'),
            '#/some3/json/pointer'
        )

        # longer JSON pointer would be picked
        rm.update(url, '3.0.0', {'#/some/json': '#/some3/json3'})
        self.assertEqual(
            rm.relocate(url, '#/some/json/pointer', '1.2', '3.0.0'),
            '#/some3/json3/pointer'
        )

    def test_with_nested_route(self):
        """ make sure nested route works
        """
        url = 'http://localhost/some/path'
        rm = SpecObjReloc()

        rm.update(url, '3.0.0', {
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
            '#/some/path/another2/two/test'
        )
        self.assertEqual(
            rm.relocate(url, '#/parameters', '2.0', '3.0.0'),
            '#/components/parameters'
        )
        self.assertEqual(
            rm.relocate(url, '#/parameters/body_1', '2.0', '3.0.0'),
            '#/components/requestBodies/body_1'
        )
        self.assertEqual(
            rm.relocate(url, '#/paths/~1p3/parameters/3', '2.0', '3.0.0'),
            '#/paths/~1p3/x-pyopenapi_internal_request_body'
        )
