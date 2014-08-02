from pyopenapi import SwaggerApp
from .utils import get_test_data_folder
from pyopenapi.obj import (
    Resource
)
import unittest


app = SwaggerApp._create_(get_test_data_folder(version='1.2', which='wordnik')) 


class SwaggerAppTestCase(unittest.TestCase):
    """ test SwaggerApp utility function """

    def test_field_name(self):
        """ field_name """
        self.assertEqual(app._schema_._field_names_, set(['info', 'authorizations', 'apiVersion', 'swaggerVersion', 'apis']))

    def test_children(self):
        """ children """
        chd = app._schema_._children_
        self.assertEqual(len(chd), 5)
        self.assertEqual(set(['user', 'pet', 'store']), set([c[0] for c in chd if isinstance(c[1], Resource)]))

