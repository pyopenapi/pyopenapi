from pyopenapi.utils import final, deref, jp_compose
from pyopenapi.migration.versions.v2_0.objects import Swagger, License, Schema, PathItem
from ....utils import get_test_data_folder, gen_test_folder_hook, SampleApp
import unittest
import os
import weakref



class ResolvePathItemTestCase(unittest.TestCase):
    """ test for PathItem $ref """

    @classmethod
    def setUpClass(kls):
        kls.app = SampleApp.create(
            get_test_data_folder(
                version='2.0',
                which=os.path.join('resolve', 'path_item')
            ),
            to_spec_version='2.0',
        )

    def test_path_item(self):
        """ make sure PathItem is correctly merged """
        a, _ = self.app.resolve_obj(jp_compose('/a', '#/paths'), from_spec_version='2.0')
        a = final(a)

        self.assertTrue(isinstance(a, PathItem))
        self.assertTrue(a.get.operationId, 'a.get')
        self.assertTrue(a.put.description, 'c.put')
        self.assertTrue(a.post.description, 'd.post')

        b, _ = self.app.resolve_obj(jp_compose('/b', '#/paths'), from_spec_version='2.0')
        b = final(b)

        self.assertTrue(b.get.operationId, 'b.get')
        self.assertTrue(b.put.description, 'c.put')
        self.assertTrue(b.post.description, 'd.post')

        c, _ = self.app.resolve_obj(jp_compose('/c', '#/paths'), from_spec_version='2.0')
        c = final(c)

        self.assertTrue(b.put.description, 'c.put')
        self.assertTrue(b.post.description, 'd.post')


class ResolveTestCase(unittest.TestCase):
    """ test for $ref other than PathItem """

    @classmethod
    def setUpClass(kls):
        kls.app = SampleApp.create(
            get_test_data_folder(
                version='2.0',
                which=os.path.join('resolve', 'other')
            ),
            to_spec_version='2.0',
        )

    def test_schema(self):
        """ make sure $ref to Schema works """
        op, _ = self.app.resolve_obj('#/paths/~1a/get', from_spec_version='2.0')
        m, _ = self.app.resolve_obj('#/definitions/d1', from_spec_version='2.0')

        self.assertEqual(
            id(op.parameters[2].schema.get_attrs('migration').ref_obj),
            id(m)
        )

    def test_response(self):
        """ make sure $ref to Response works """
        p, _ = self.app.resolve_obj('#/paths/~1a/get', from_spec_version='2.0')

        self.assertEqual(deref(p.responses['default']).description, 'void, r1')

    def test_raises(self):
        """ make sure to raise for invalid input """
        self.assertRaises(ValueError, self.app.resolve_obj, None, from_spec_version='2.0')
        self.assertRaises(ValueError, self.app.resolve_obj, '', from_spec_version='2.0')


class DerefTestCase(unittest.TestCase):
    """ test for pyopenapi.utils.deref """

    @classmethod
    def setUpClass(kls):
        kls.app = SampleApp.create(
            get_test_data_folder(
                version='2.0',
                which=os.path.join('resolve', 'deref')
            ),
            to_spec_version='2.0'
        )

    def test_deref(self):
        od, _ = self.app.resolve_obj('#/definitions/s1', from_spec_version='2.0')
        od = deref(od)

        m, _ = self.app.resolve_obj('#/definitions/s4', from_spec_version='2.0')
        self.assertEqual(id(od), id(m))

    def test_external_ref_loading_order(self):
        """ make sure pyopenapi.spec_obj_store would remove
        dummy objects when resolving.

        dummy objects: an spec object co-exist with its parent in
        pyopenapi.spec_obj_store
        """

        # prepare a dummy app
        app = SampleApp.load(
            url='file:///ex/root/swagger.json',
            url_load_hook=gen_test_folder_hook(get_test_data_folder(version='2.0')),
        )

        # fill its cache with several dummy objects
        license, _ = app.resolve_obj('file:///wordnik/swagger.json#/info/license',
            parser=License,
            from_spec_version='2.0',
            remove_dummy=True,
        )
        order, _ = app.resolve_obj('file:///wordnik/swagger.json#/definitions/Order',
            parser=Schema,
            from_spec_version='2.0',
            remove_dummy=True,
        )
        pet, _ = app.resolve_obj('file:///wordnik/swagger.json#/definitions/Pet',
            parser=Schema,
            from_spec_version='2.0',
            remove_dummy=True,
        )

        # resolve their root object with latest version
        swg, _ = app.resolve_obj('file:///wordnik/swagger.json',
            parser=Schema,
            from_spec_version='2.0',
            remove_dummy=True,
        )

        # make sure root objec use those dummy objects during loading
        self.assertEqual(weakref.proxy(swg.resolve(['info','license'])), license)
        self.assertEqual(weakref.proxy(swg.resolve(['definitions','Order'])), order)
        self.assertEqual(weakref.proxy(swg.resolve(['definitions','Pet'])), pet)

        # make sure this relation is maintained after migrating up
        license, _ = app.resolve_obj('file:///wordnik/swagger.json#/info/license',
            parser=License,
            from_spec_version='2.0',
            to_spec_version='3.0.0',
            remove_dummy=True,
        )

        # #/definitios/Order is changed to #/components/schemas/Order
        # this case is not taken care here.

        # resolve their root object with latest version
        oai, _ = app.resolve_obj('file:///wordnik/swagger.json',
            from_spec_version='2.0',
            to_spec_version='3.0.0',
            remove_dummy=True,
        )

        # make sure root objec use those dummy objects during loading
        self.assertEqual(weakref.proxy(oai.resolve(['info', 'license'])), license)

