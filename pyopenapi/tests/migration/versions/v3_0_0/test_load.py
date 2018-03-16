# -*- coding: utf-8 -*-
import unittest
import yaml

from pyopenapi.migration.versions.v3_0_0.objects import OpenApi
from ....utils import get_test_file


# pylint: disable=invalid-name
class Load_3_0_0_SpecTestCase(unittest.TestCase):
    """ test loading open-api 3.0 spec
    """

    def test_api_with_examples(self):
        """ load api-with-examples.yaml
        """
        try:
            OpenApi(
                yaml.load(
                    get_test_file(
                        version='3.0.0',
                        which='openapi',
                        file_name='api-with-examples.yaml')),
                path='#')
        except:
            self.fail('unable to load api-with-examples.yaml')
            raise

    def test_petstore_expanded(self):
        """ load petstore-expanded.yaml
        """
        try:
            OpenApi(
                yaml.load(
                    get_test_file(
                        version='3.0.0',
                        which='openapi',
                        file_name='petstore-expanded.yaml')),
                path='#')
        except:
            self.fail('unable to load petstore-expanded.yaml')
            raise

    def test_petstore(self):
        """ load pestore.yaml
        """
        try:
            OpenApi(
                yaml.load(
                    get_test_file(
                        version='3.0.0',
                        which='openapi',
                        file_name='petstore.yaml')),
                path='#')
        except:
            self.fail('unable to load petstore.yaml')
            raise

    def test_uber(self):
        """ load uber.yaml
        """
        try:
            OpenApi(
                yaml.load(
                    get_test_file(
                        version='3.0.0', which='openapi',
                        file_name='uber.yaml')),
                path='#')
        except:
            self.fail('unable to load uber.yaml')
            raise

    def test_link_example(self):
        """ load link-example.yaml
        """
        try:
            OpenApi(
                yaml.load(
                    get_test_file(
                        version='3.0.0',
                        which='openapi',
                        file_name='link-example.yaml')),
                path='#')
        except:
            self.fail('unable to load link-example.yaml')
            raise
