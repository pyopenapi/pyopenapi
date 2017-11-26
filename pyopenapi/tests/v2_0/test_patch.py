from pyopenapi import App
from ..utils import get_test_data_folder
from ...utils import final, deref
import unittest


_json = 'application/json'
_xml = 'application/xml'


class PatchObjTestCase(unittest.TestCase):
    """ test patch_obj.py """

    @classmethod
    def setUpClass(kls):
        kls.app = App._create_(get_test_data_folder(
            version='2.0',
            which='patch'
        ))

    def test_operation_produces_consumes(self):
        """ test patch Operation with produces and
        consumes
        """
        p = self.app.s('/pc')

        self.assertTrue(_json in p.get.request_body.content)
        self.assertTrue(_json in p.get.responses['default'].content)
        self.assertTrue(_xml in p.post.responses['default'].content)
        self.assertTrue(_json in p.post.request_body.content)
        self.assertTrue(_json in p.put.responses['default'].content)
        self.assertTrue(_xml in p.put.request_body.content)
        self.assertTrue(_xml in p.delete.responses['default'].content)
        self.assertTrue(_xml in p.delete.request_body.content)

    def test_operation_parameters(self):
        """ test patch Operation with parameters """
        p = self.app.s('/param')

        pp = final(p.get).parameters
        self.assertEqual(len(pp), 2)

        self.assertEqual(pp[0].name, 'p1')
        self.assertEqual(getattr(pp[0], 'in'), 'query')
        self.assertEqual(getattr(pp[0].schema, 'type'), 'string')
        self.assertEqual(pp[1].name, 'p2')
        self.assertEqual(getattr(pp[1], 'in'), 'query')
        self.assertEqual(getattr(pp[1].schema, 'type'), 'string')

        pp = final(p.post).parameters
        self.assertEqual(len(pp), 3)

        self.assertEqual(pp[0].name, 'p1')
        self.assertEqual(getattr(pp[0], 'in'), 'path')
        self.assertEqual(getattr(pp[0].schema, 'type'), 'string')
        self.assertEqual(pp[1].name, 'p1')
        self.assertEqual(getattr(pp[1], 'in'), 'query')
        self.assertEqual(getattr(pp[1].schema, 'type'), 'string')
        self.assertEqual(pp[2].name, 'p2')
        self.assertEqual(getattr(pp[2], 'in'), 'query')
        self.assertEqual(getattr(pp[2].schema, 'type'), 'string')

    def test_operation_scheme(self):
        """ test patch Operation with scheme """
        p = self.app.s('/s')

        self.assertEqual(p.get.cached_schemes, self.app.root.schemes)
        self.assertEqual(p.get.cached_schemes, ['http', 'https'])

    def test_operation_security(self):
        """ test patch Operation with Swagger.security """
        p = self.app.s('/op_security')

        # when security is something, do not overwrite
        self.assertTrue(len(p.put.security) == 1)
        self.assertTrue("internalApiKey" in p.put.security[0])
        # when security is [], do not overwrite
        self.assertEqual(p.get.security, [])
        # when security is not provided, overwrite with global
        self.assertTrue(len(p.post.security) == 2)
        self.assertTrue("githubAccessCode" in p.post.security[0])
        self.assertTrue("internalApiKey" in p.post.security[1])

    def test_path_item(self):
        """ test patch PathItem """
        p = self.app.s('/pc')

        self.assertEqual(p.get.method, 'get')
        self.assertEqual(p.get.url, '//test.com/v1/pc')
        self.assertEqual(p.get.path, '/pc')
        self.assertEqual(p.get.base_path, '/v1')

    def test_schema(self):
        """ test patch Schema """
        s = self.app.resolve('#/components/schemas/schema1')

        self.assertEqual(s.name, 'schema1')
