from pyopenapi.migration.scan import Scanner2
from pyopenapi.migration.versions.v2_0.scanner import YamlFixer
from pyopenapi.migration.versions.v2_0.objects import Operation
from ..utils import get_test_data_folder, SampleApp
import unittest


class YAMLTestCase(unittest.TestCase):
    """ test yaml loader support """

    def test_load(self):
        """ make sure the result of yaml and json are identical """
        app_json = SampleApp.load(
            get_test_data_folder(
                version='2.0',
                which='wordnik'
            )
        )
        app_yaml = SampleApp.load(
            get_test_data_folder(
                version='2.0',
                which='yaml',
            )
        )
        s = Scanner2()
        s.scan(route=[YamlFixer()], root=app_yaml.raw, leaves=[Operation])

        self.assertEqual((True, ''), app_json.raw.compare(app_yaml.raw))

