from pyopenapi import SwaggerApp
from .utils import get_test_data_folder
import pyopenapi
import unittest
import httpretty
import os


class SwaggerCoreTestCase(unittest.TestCase):
    """ test core part """

    def test_backward_compatible_v1_2(self):
        """ make sure alias works """
        self.assertEqual(pyopenapi.SwaggerAuth, pyopenapi.SwaggerSecurity)
        self.assertEqual(pyopenapi.SwaggerApp._create_, pyopenapi.SwaggerApp.create)

    @httpretty.activate
    def test_auto_schemes(self):
        """ make sure we scheme of url to access
        swagger.json as default scheme
        """
        # load swagger.json
        data = None
        with open(os.path.join(get_test_data_folder(
                version='2.0',
                which=os.path.join('schema', 'model')
                ), 'swagger.json')) as f:
            data = f.read()

        httpretty.register_uri(
            httpretty.GET,
            'http://test.com/api-doc/swagger.json',
            body=data
        )

        app = SwaggerApp._create_('http://test.com/api-doc/swagger.json')
        self.assertEqual(app.schemes, ['http'])
