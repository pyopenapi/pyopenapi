# -*- coding: utf-8 -*-
import unittest
import os
import weakref

from pyopenapi.utils import final, deref, jp_compose
from pyopenapi.migration.versions.v2_0.objects import License, Schema, PathItem
from ....utils import get_test_data_folder, gen_test_folder_hook, SampleApp


class ResolvePathItemTestCase(unittest.TestCase):
    """ test for PathItem $ref """

    @classmethod
    def setUpClass(cls):
        cls.app = SampleApp.create(
            get_test_data_folder(
                version='2.0', which=os.path.join('resolve', 'path_item')),
            to_spec_version='2.0',
        )

    def test_path_item(self):
        """ make sure PathItem is correctly merged """
        path_item_a, _ = self.app.resolve_obj(
            jp_compose('/a', '#/paths'), from_spec_version='2.0')
        path_item_a = final(path_item_a)

        self.assertTrue(isinstance(path_item_a, PathItem))
        self.assertTrue(path_item_a.get.operationId, 'a.get')
        self.assertTrue(path_item_a.put.description, 'c.put')
        self.assertTrue(path_item_a.post.description, 'd.post')

        path_item_b, _ = self.app.resolve_obj(
            jp_compose('/b', '#/paths'), from_spec_version='2.0')
        path_item_b = final(path_item_b)

        self.assertTrue(path_item_b.get.operationId, 'b.get')
        self.assertTrue(path_item_b.put.description, 'c.put')
        self.assertTrue(path_item_b.post.description, 'd.post')

        path_item_c, _ = self.app.resolve_obj(
            jp_compose('/c', '#/paths'), from_spec_version='2.0')
        path_item_c = final(path_item_c)

        self.assertTrue(path_item_b.put.description, 'c.put')
        self.assertTrue(path_item_b.post.description, 'd.post')


class ResolveTestCase(unittest.TestCase):
    """ test for $ref other than PathItem """

    @classmethod
    def setUpClass(cls):
        cls.app = SampleApp.create(
            get_test_data_folder(
                version='2.0', which=os.path.join('resolve', 'other')),
            to_spec_version='2.0',
        )

    def test_schema(self):
        """ make sure $ref to Schema works """
        operation, _ = self.app.resolve_obj(
            '#/paths/~1a/get', from_spec_version='2.0')
        schema, _ = self.app.resolve_obj(
            '#/definitions/d1', from_spec_version='2.0')

        self.assertEqual(
            id(operation.parameters[2].schema.get_attrs('migration').ref_obj),
            id(schema))

    def test_response(self):
        """ make sure $ref to Response works """
        operation, _ = self.app.resolve_obj(
            '#/paths/~1a/get', from_spec_version='2.0')

        self.assertEqual(
            deref(operation.responses['default']).description, 'void, r1')

    def test_raises(self):
        """ make sure to raise for invalid input """
        self.assertRaises(
            ValueError, self.app.resolve_obj, None, from_spec_version='2.0')
        self.assertRaises(
            ValueError, self.app.resolve_obj, '', from_spec_version='2.0')


class DerefTestCase(unittest.TestCase):
    """ test for pyopenapi.utils.deref """

    @classmethod
    def setUpClass(cls):
        cls.app = SampleApp.create(
            get_test_data_folder(
                version='2.0', which=os.path.join('resolve', 'deref')),
            to_spec_version='2.0')

    def test_deref(self):
        schema_1, _ = self.app.resolve_obj(
            '#/definitions/s1', from_spec_version='2.0')
        schema_1 = deref(schema_1)

        schema_4, _ = self.app.resolve_obj(
            '#/definitions/s4', from_spec_version='2.0')
        self.assertEqual(id(schema_1), id(schema_4))

    def test_external_ref_loading_order(self):
        """ make sure pyopenapi.spec_obj_store would remove
        dummy objects when resolving.

        dummy objects: an spec object co-exist with its parent in
        pyopenapi.spec_obj_store
        """

        # prepare a dummy app
        app = SampleApp.load(
            url='file:///ex/root/swagger.json',
            url_load_hook=gen_test_folder_hook(
                get_test_data_folder(version='2.0')),
        )

        # fill its cache with several dummy objects
        license_, _ = app.resolve_obj(
            'file:///wordnik/swagger.json#/info/license',
            parser=License,
            from_spec_version='2.0',
            remove_dummy=True,
        )
        order, _ = app.resolve_obj(
            'file:///wordnik/swagger.json#/definitions/Order',
            parser=Schema,
            from_spec_version='2.0',
            remove_dummy=True,
        )
        pet, _ = app.resolve_obj(
            'file:///wordnik/swagger.json#/definitions/Pet',
            parser=Schema,
            from_spec_version='2.0',
            remove_dummy=True,
        )

        # resolve their root object with latest version
        swg, _ = app.resolve_obj(
            'file:///wordnik/swagger.json',
            parser=Schema,
            from_spec_version='2.0',
            remove_dummy=True,
        )

        # make sure root objec use those dummy objects during loading
        self.assertEqual(
            weakref.proxy(swg.resolve(['info', 'license'])), license_)
        self.assertEqual(
            weakref.proxy(swg.resolve(['definitions', 'Order'])), order)
        self.assertEqual(
            weakref.proxy(swg.resolve(['definitions', 'Pet'])), pet)

        # make sure this relation is maintained after migrating up
        license_, _ = app.resolve_obj(
            'file:///wordnik/swagger.json#/info/license',
            parser=License,
            from_spec_version='2.0',
            to_spec_version='3.0.0',
            remove_dummy=True,
        )

        # #/definitios/Order is changed to #/components/schemas/Order
        # this case is not taken care here.

        # resolve their root object with latest version
        root, _ = app.resolve_obj(
            'file:///wordnik/swagger.json',
            from_spec_version='2.0',
            to_spec_version='3.0.0',
            remove_dummy=True,
        )

        # make sure root objec use those dummy objects during loading
        self.assertEqual(
            weakref.proxy(root.resolve(['info', 'license'])), license_)
