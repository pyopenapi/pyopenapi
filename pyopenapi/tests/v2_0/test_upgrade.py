from ..utils import get_test_data_folder
from ...core import App
from ...scanner.v2_0.upgrade import converters
import unittest
import os
import six


app = App.load(get_test_data_folder(
    version='2.0',
    which='upgrade'
))
app.prepare(strict=False)

class ExternalDocConverterTestCase(unittest.TestCase):
    """ test case for externalDoc converter """

    def test_external_doc(self):
        ex_doc = app.resolve('#/externalDocs')

        obj = converters.to_external_docs(ex_doc, '')
        self.assertTrue('url' in obj)
        self.assertEqual(obj['url'], ex_doc.url)
        self.assertTrue('description' in obj)
        self.assertEqual(obj['description'], ex_doc.description)

