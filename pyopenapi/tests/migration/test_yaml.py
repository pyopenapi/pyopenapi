# -*- coding: utf-8 -*-
import unittest

from pyopenapi.migration.scan import scan
from pyopenapi.migration.versions.v2_0.scanner import YamlFixer
from pyopenapi.migration.versions.v2_0.objects import Operation
from ..utils import get_test_data_folder, SampleApp


class YAMLTestCase(unittest.TestCase):
    """ test yaml loader support """

    def test_load(self):
        """ make sure the result of yaml and json are identical """
        app_json = SampleApp.load(
            get_test_data_folder(version='2.0', which='wordnik'))
        app_yaml = SampleApp.load(
            get_test_data_folder(
                version='2.0',
                which='yaml',
            ))
        scan(route=[YamlFixer()], root=app_yaml.raw, leaves=[Operation])

        self.assertEqual((True, ''), app_json.raw.compare(app_yaml.raw))
