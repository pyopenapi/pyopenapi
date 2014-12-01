import pyopenapi
import unittest


class SwaggerCoreTestCase(unittest.TestCase):
    """ test core part """

    def test_auth_security(self):
        """ make sure alias works """
        self.assertEqual(pyopenapi.SwaggerAuth, pyopenapi.SwaggerSecurity)

