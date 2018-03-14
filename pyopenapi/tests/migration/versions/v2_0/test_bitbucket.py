import unittest

from ....utils import get_test_data_folder, SampleApp


class BitBucketTestCase(unittest.TestCase):
    """ test for bitbucket related """

    @classmethod
    def setUpClass(cls):
        cls.app = SampleApp.create(
            get_test_data_folder(version='2.0', which='bitbucket'),
            to_spec_version='2.0')

    def test_load(self):
        # make sure loading is fine,
        # this test case could be removed when something else exists in this suite.
        pass
