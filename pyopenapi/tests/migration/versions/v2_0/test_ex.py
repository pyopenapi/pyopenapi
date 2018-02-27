from pyopenapi.migration.utils import deref, final
from pyopenapi.migration.versions.v2_0.objects import PathItem
from ....utils import get_test_data_folder, gen_test_folder_hook, SampleApp
import unittest


class ExternalDocumentTestCase(unittest.TestCase):
    """ test case for external document """

    @classmethod
    def setUpClass(kls):
        kls.app = SampleApp.create(
            url='file:///root/swagger.json',
            url_load_hook=gen_test_folder_hook(get_test_data_folder(version='2.0', which='ex')),
            to_spec_version='2.0',
        )

    def test_resolve(self):
        """ make sure resolve with full JSON reference
        is the same as resolve with JSON pointer.
        """
        p1, _ = self.app.resolve_obj('#/paths/~1full', from_spec_version='2.0')
        p2, _ = self.app.resolve_obj('file:///root/swagger.json#/paths/~1full', from_spec_version='2.0')
        # refer to
        #      http://stackoverflow.com/questions/10246116/python-dereferencing-weakproxy
        # for how to dereferencing weakref
        self.assertEqual(p1.__repr__(), p2.__repr__())

    def test_full_path_item(self):
        """ make sure PathItem is correctly merged
        """
        p, _ = self.app.resolve_obj('#/paths/~1full', from_spec_version='2.0')
        p_final = final(p)

        self.assertNotEqual(p_final.get, None)
        self.assertTrue('default' in p_final.get.responses)
        self.assertTrue('404' in p_final.get.responses)

        another_p, _ = self.app.resolve_obj(
            'file:///full/swagger.json#/paths/~1user',
            parser=PathItem,
            from_spec_version='2.0'
        )
        self.assertNotEqual(id(p), id(another_p))
        self.assertTrue('default' in another_p.get.responses)
        self.assertTrue('404' in another_p.get.responses)

    def test_partial_schema(self):
        """  make sure partial swagger.json with Schema
        loaded correctly.
        """
        p, _ = self.app.resolve_obj('#/definitions/s4', from_spec_version='2.0')
        original_p, _ = self.app.resolve_obj(
            'file:///partial/schema/swagger.json',
            from_spec_version='2.0',
        )

        # refer to
        #      http://stackoverflow.com/questions/10246116/python-dereferencing-weakproxy
        # for how to dereferencing weakref
        self.assertEqual(p.items.get_attrs('migration').ref_obj.__repr__(), original_p.__repr__())

        p_, _ = self.app.resolve_obj('#/definitions/s3', from_spec_version='2.0')
        self.assertEqual(p_.__repr__(), original_p.items.get_attrs('migration').ref_obj.__repr__())

    def test_relative_path_item(self):
        """ make sure that relative file schema works
           https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#relative-schema-file-example
        """
        def chk(obj):
            self.assertEqual(obj.get.responses['default'].description, 'relative, path_item, get, response')
            self.assertEqual(obj.put.responses['default'].description, 'relative, path_item, put, response')

        o, _ = self.app.resolve_obj('#/paths/~1relative', from_spec_version='2.0')
        chk(final(o))

        o, _ = self.app.resolve_obj('file:///root/path_item.json', from_spec_version='2.0')
        chk(final(o))

    def test_relative_schema(self):
        """ test case for issue#53,
        relative file, which root is a Schema Object
        """
        app = SampleApp.create(
            url='file:///relative/internal.yaml',
            url_load_hook=gen_test_folder_hook(get_test_data_folder(version='2.0', which='ex')),
            to_spec_version='2.0',
        )


class ReuseTestCase(unittest.TestCase):
    """ test case for 'reuse', lots of partial swagger document
        https://github.com/OAI/OpenAPI-Specification/blob/master/guidelines/REUSE.md#guidelines-for-referencing
    """
    @classmethod
    def setUpClass(kls):
        kls.app = SampleApp.create(
            url='file:///reuse/swagger.json',
            url_load_hook=gen_test_folder_hook(get_test_data_folder(version='2.0', which='ex')),
            to_spec_version='2.0',
        )

    def test_relative_folder(self):
        """ make sure the url prepend on $ref should be
        derived from the path of current document
        """
        o, _ = self.app.resolve_obj('#/definitions/QQ', from_spec_version='2.0')
        o = deref(o)

        self.assertEqual(o.description, 'Another simple model')

