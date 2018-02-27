from pyopenapi.migration.utils import jr_split, normalize_url
from pyopenapi.migration.versions.v3_0_0.objects import (
    Reference, Schema, Parameter,
    Header, RequestBody, Response,
    Link, Callback, PathItem,
    Operation, SecurityScheme,
    )
from ....utils import get_test_data_folder, gen_test_folder_hook, SampleApp
import unittest


class PathItemMergeTestCase(unittest.TestCase):
    """ test case for merging external path item """

    @classmethod
    def setUpClass(kls):
        kls.app = SampleApp.create(
            url='file:///root.yml',
            url_load_hook=gen_test_folder_hook(get_test_data_folder(version='3.0.0', which='external')),
            to_spec_version='3.0.0'
        )

    def test_merge_basic(self):
        """ one path item in root ref to an external path item
        """
        pi, _ = self.app.resolve_obj(
            '#/paths/~1test1',
            from_spec_version='3.0.0',
        )

        def _not_exist(o):
            self.assertEqual(o.delete, None)
            self.assertEqual(o.options, None)
            self.assertEqual(o.head, None)
            self.assertEqual(o.patch, None)
            self.assertEqual(o.trace, None)

        # check original object is not touch, or 'dump' would be wrong
        _not_exist(pi)
        self.assertNotEqual(pi.post, None)

        another, _ = self.app.resolve_obj(
            'file:///partial_path_item_1.yml#/test1',
            parser=PathItem,
            from_spec_version='3.0.0',
        )
        self.assertNotEqual(another.get, None)
        self.assertNotEqual(another.put, None)

        final = pi.get_attrs('migration').final_obj
        _not_exist(final)
        self.assertNotEqual(final.get, None)
        self.assertNotEqual(final.post, None)
        # children objects are shared
        self.assertEqual(id(pi.post), id(final.post))
        self.assertEqual(id(another.get), id(final.get))
        self.assertEqual(id(another.put), id(final.put))

    def test_merge_cascade(self):
        """ path item in root ref to an external path item with
        ref to yet another path item, too
        """

        pi, _ = self.app.resolve_obj(
            '#/paths/~1test2',
            from_spec_version='3.0.0',
        )

        def _not_exist(o):
            self.assertEqual(o.put, None)
            self.assertEqual(o.delete, None)
            self.assertEqual(o.options, None)
            self.assertEqual(o.head, None)
            self.assertEqual(o.patch, None)
            self.assertEqual(o.trace, None)

        _not_exist(pi)
        self.assertEqual(pi.get, None)
        self.assertEqual(pi.post, None)

        another_1, _ = self.app.resolve_obj(
            'file:///partial_path_item_1.yml#/test2',
            from_spec_version='3.0.0',
        )
        _not_exist(another_1)
        self.assertNotEqual(another_1.get, None)
        self.assertEqual(another_1.post, None)

        another_2, _ = self.app.resolve_obj(
            'file:///partial_path_item_2.yml#/test2',
            from_spec_version='3.0.0',
        )
        _not_exist(another_2)
        self.assertEqual(another_2.get, None)
        self.assertNotEqual(another_2.post, None)

        final = pi.get_attrs('migration').final_obj
        _not_exist(final)
        self.assertNotEqual(final.get, None)
        self.assertNotEqual(final.post, None)
        self.assertEqual(id(final.get), id(another_1.get))
        self.assertEqual(id(final.post), id(another_2.post))

    def test_no_ref_should_not_have_final(self):
        """ path item object without $ref
        should not have 'final_obj' property
        """
        pi, _ = self.app.resolve_obj(
            'file:///partial_path_item_2.yml#/test2',
            from_spec_version='3.0.0',
        )
        self.assertEqual(pi.get_attrs('migration').final_obj, None)

    def test_path_item_parameters(self):
        """ make sure parameters in path-item are handled
        """
        test4, _ = self.app.resolve_obj(
            '#/paths/~1test4',
            from_spec_version='3.0.0',
        )

        p = test4.parameters[0]
        self.assertTrue(isinstance(p, Reference))
        self.assertNotEqual(p.get_attrs('migration').ref_obj, None)

        p = test4.parameters[1]
        self.assertTrue(isinstance(p, Reference))
        self.assertNotEqual(p.get_attrs('migration').ref_obj, None)


class ResolveTestCase(unittest.TestCase):
    """ test cases related to 'resolving' stuffs
    """

    @classmethod
    def setUpClass(kls):
        kls.app = SampleApp.create(
            url='file:///root.yml',
            url_load_hook=gen_test_folder_hook(get_test_data_folder(version='3.0.0', which='external')),
            to_spec_version='3.0.0'
        )

    def test_normalized_ref(self):
        """ make sure all '$ref' are cached with a normalized one
        """
        test1, _ = self.app.resolve_obj(
            '#/paths/~1test1',
            parser=PathItem,
            from_spec_version='3.0.0',
        )
        resp = test1.post.responses['default']

        self.assertTrue(isinstance(resp, Reference))
        self.assertEqual(
            resp.get_attrs('migration').normalized_ref,
            'file:///root.yml#/components/responses/void'
        )

    def test_resolve_schema(self):
        """ make sure 'Schema' is resolved and cached
        """
        s, _ = self.app.resolve_obj(
            '#/components/schemas/partial_1',
            from_spec_version='3.0.0',
        )
        self.assertTrue(isinstance(s, Reference))
        self.assertEqual(
            s.get_attrs('migration').normalized_ref,
            'file:///partial_1.yml#/schemas/partial_1'
        )
        self.assertTrue(isinstance(s.get_attrs('migration').ref_obj, Schema))
        self.assertEqual(s.get_attrs('migration').ref_obj.type_, 'string')

    def test_resolve_parameter(self):
        """ make sure 'Parameter' is resolved and cached
        """
        p, _ = self.app.resolve_obj(
            '#/paths/~1test3/get/parameters/0',
            from_spec_version='3.0.0',
        )
        self.assertEqual(
            p.get_attrs('migration').normalized_ref,
            'file:///root.yml#/components/parameters/test3.p1'
        )
        self.assertTrue(isinstance(p.get_attrs('migration').ref_obj, Reference))

        p = p.get_attrs('migration').ref_obj
        self.assertEqual(
            p.get_attrs('migration').normalized_ref,
            'file:///partial_1.yml#/parameters/test3.p1'
        )
        self.assertTrue(isinstance(p.get_attrs('migration').ref_obj, Parameter))

        p = p.get_attrs('migration').ref_obj
        self.assertEqual(p.in_, 'query')

        s = p.schema
        self.assertTrue(isinstance(s, Reference))
        self.assertEqual(
            s.get_attrs('migration').normalized_ref,
            'file:///partial_2.yml#/schemas/test3.p1.schema'
        )

        s = s.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(s, Schema))
        self.assertEqual(s.type_, 'string')
        self.assertEqual(s.format_, 'password')

    def test_resolve_header(self):
        """ make sure 'Header' is resolved and cached
        """
        p, _ = self.app.resolve_obj(
            '#/paths/~1test3/delete/parameters/0',
            from_spec_version='3.0.0',
        )
        self.assertTrue(isinstance(p, Reference))
        self.assertEqual(
            p.get_attrs('migration').normalized_ref,
            'file:///root.yml#/components/headers/test3.header.1'
        )

        p = p.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(p, Reference))
        self.assertEqual(
            p.get_attrs('migration').normalized_ref,
            'file:///partial_1.yml#/headers/test3.header.1'
        )

        h = p.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(h, Header))
        self.assertEqual(h.in_, 'header')
        self.assertEqual(h.name, None)
        self.assertTrue(isinstance(h.schema, Reference))
        self.assertEqual(
            h.schema.get_attrs('migration').normalized_ref,
            'file:///partial_2.yml#/schemas/test3.header.1.schema'
        )

        s = h.schema.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(s, Schema))
        self.assertEqual(s.type_, 'integer')
        self.assertEqual(s.format_, 'int32')

    def test_resolve_request_body(self):
        """ make sure 'RequestBody' is resolved and cached
        """
        b, _ = self.app.resolve_obj(
            '#/paths/~1test3/post/requestBody',
            from_spec_version='3.0.0',
        )
        self.assertTrue(isinstance(b, Reference))
        self.assertEqual(
            b.get_attrs('migration').normalized_ref,
            'file:///root.yml#/components/requestBodies/test3.body.1'
        )

        b = b.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(b, Reference))
        self.assertEqual(
            b.get_attrs('migration').normalized_ref,
            'file:///partial_1.yml#/bodies/test3.body.1'
        )

        b = b.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(b, RequestBody))
        self.assertTrue('application/json' in b.content)

        s = b.content['application/json'].schema
        self.assertTrue(isinstance(s, Reference))
        self.assertEqual(
            s.get_attrs('migration').normalized_ref,
            'file:///root.yml#/components/schemas/test3.body.1.schema.1'
        )

        s = s.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(s, Reference))
        self.assertEqual(
            s.get_attrs('migration').normalized_ref,
            'file:///partial_2.yml#/schemas/test3.body.1.schema.1'
        )

        s = s.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(s, Schema))
        self.assertEqual(s.type_, 'object')
        self.assertTrue('email' in s.properties)
        self.assertEqual(s.properties['email'].type_, 'string')
        self.assertTrue('password' in s.properties)
        self.assertEqual(s.properties['password'].type_, 'string')
        self.assertEqual(s.properties['password'].format_, 'password')

    def test_resolve_response(self):
        """ make sure 'Response' is resolved and cached
        """
        r, _ = self.app.resolve_obj(
            '#/paths/~1test3/get/responses/400',
            from_spec_version='3.0.0',
        )
        self.assertTrue(isinstance(r, Reference))
        self.assertEqual(
            r.get_attrs('migration').normalized_ref,
            'file:///root.yml#/components/responses/BadRequest'
        )

        r = r.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(r, Reference))
        self.assertEqual(
            r.get_attrs('migration').normalized_ref,
            'file:///partial_1.yml#/responses/test3.get.response.400'
        )

        r = r.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(r, Response))
        self.assertEqual(r.description, 'test description')
        self.assertTrue('test-x-device-id' in r.headers)
        self.assertTrue('some-link' in r.links)

        h = r.headers['test-x-device-id']
        self.assertTrue(isinstance(h, Reference))
        h = h.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(h, Header))
        self.assertEqual(h.schema.type_, 'string')

        lk = r.links['some-link']
        self.assertTrue(isinstance(lk, Reference))
        lk = lk.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(lk, Link))
        self.assertEqual(lk.operation_ref, 'file:///root.yml#/paths/~1test1/post')
        self.assertTrue('id_1' in lk.parameters)
        self.assertEqual(lk.parameters['id_1'], '$response.body#/id_1')

    def test_resolve_components_callback(self):
        """ make sure 'Callback' in components is resolved and cached
        """
        cb, _ = self.app.resolve_obj(
            '#/components/callbacks/cb.1',
            from_spec_version='3.0.0',
        )
        self.assertTrue(isinstance(cb, Reference))
        self.assertEqual(
            cb.get_attrs('migration').normalized_ref,
            'file:///partial_1.yml#/callbacks/cb.1'
        )

        cb = cb.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(cb, Callback))
        self.assertEqual(cb['/test-cb-1'].summary, 'some test path item for callback')

        pi = cb['/test-cb-1'].get
        self.assertEqual(pi.operation_id, 'cb.1.get')
        p = pi.parameters[0]
        self.assertEqual(p.name, 'cb.1.p.1')
        self.assertEqual(p.in_, 'query')
        self.assertEqual(p.schema.type_, 'string')

        r = pi.responses['default']
        self.assertTrue(isinstance(r, Reference))
        self.assertEqual(
            r.get_attrs('migration').normalized_ref,
            'file:///root.yml#/components/responses/void'
        )

        r = r.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(r, Response))
        self.assertEqual(r.description, 'void response')

        # able to resolve PathItem under callback
        p, _ = self.app.resolve_obj(
            'file:///partial_1.yml#/callbacks/cb.1/~1test-cb-1',
            from_spec_version='3.0.0',
        )
        self.assertTrue(isinstance(p, PathItem))


class ResolveWithObjectRelocationTestCase(unittest.TestCase):
    """ test case for App.resolve with object relocation
    """

    @classmethod
    def setUpClass(kls):
        doc_path = get_test_data_folder(
            version='2.0',
            which='upgrade',
        )

        kls.app = SampleApp.create(doc_path, to_spec_version='3.0.0')
        kls.doc_path = normalize_url(doc_path)

    def test_operation(self):
        """ operation should not be changed
        """
        jref = '#/paths/~1p1/get'
        op, new_ref = self.app.resolve_obj(
            jref, from_spec_version='2.0', to_spec_version='3.0.0'
        )
        url, jp = jr_split(new_ref)
        self.assertEqual(jp, jref)
        self.assertEqual(url, self.doc_path)
        self.assertTrue(isinstance(op, Operation))

    def test_swagger_parameter(self):
        """ parameters -> components/parameters
        """
        p, new_ref = self.app.resolve_obj(
            '#/parameters/query_string', from_spec_version='2.0', to_spec_version='3.0.0'
        )
        url, jp = jr_split(new_ref)
        self.assertEqual(url, self.doc_path)
        self.assertEqual(jp, '#/components/parameters/query_string')
        self.assertTrue(isinstance(p, Parameter))

    def test_swagger_body_parameter(self):
        """ parameters -> components/requestBodies
        """
        bp, new_ref = self.app.resolve_obj(
            '#/parameters/body_file_ref', from_spec_version='2.0', to_spec_version='3.0.0'
        )
        url, jp = jr_split(new_ref)
        self.assertEqual(url, self.doc_path)
        self.assertEqual(jp, '#/components/requestBodies/body_file_ref')
        self.assertTrue(isinstance(bp, RequestBody))

    def test_swagger_form_parameter(self):
        """ parameters -> components/requestBodies
        """
        fp, new_ref = self.app.resolve_obj(
            '#/parameters/form_string', from_spec_version='2.0', to_spec_version='3.0.0'
        )
        url, jp = jr_split(new_ref)
        self.assertEqual(url, self.doc_path)
        self.assertEqual(jp, '#/components/requestBodies/form_string')
        self.assertTrue(isinstance(fp, RequestBody))

    def test_swagger_response(self):
        """ responses -> components/responses
        """
        vd, new_ref = self.app.resolve_obj(
            '#/responses/void', from_spec_version='2.0', to_spec_version='3.0.0'
        )
        url, jp = jr_split(new_ref)
        self.assertEqual(url, self.doc_path)
        self.assertEqual(jp, '#/components/responses/void')
        self.assertTrue(isinstance(vd, Response))

    def test_swagger_definitions(self):
        """ definitions -> components/schemas
        """
        d, new_ref = self.app.resolve_obj(
            '#/definitions/category', from_spec_version='2.0', to_spec_version='3.0.0'
        )
        url, jp = jr_split(new_ref)
        self.assertEqual(url, self.doc_path)
        self.assertEqual(jp, '#/components/schemas/category')
        self.assertTrue(isinstance(d, Schema))

    def test_swagger_security_definitions(self):
        """ securityDefinitions -> components/securitySchemes
        """
        s, new_ref = self.app.resolve_obj(
            '#/securityDefinitions/petstore_auth', from_spec_version='2.0', to_spec_version='3.0.0'
        )
        url, jp = jr_split(new_ref)
        self.assertEqual(url, self.doc_path)
        self.assertEqual(jp, '#/components/securitySchemes/petstore_auth')
        self.assertTrue(isinstance(s, SecurityScheme))

    def test_path_item_body_parameters(self):
        """ body paraemter under 'PathItem' object
        should support object relocation, too
        """
        p, new_ref = self.app.resolve_obj(
            '#/paths/~1p3~1{user_name}/parameters/0', from_spec_version='2.0', to_spec_version='3.0.0'
        )
        url, jp = jr_split(new_ref)
        self.assertEqual(url, self.doc_path)
        self.assertEqual(jp, '#/paths/~1p3~1{user_name}/x-pyopenapi_internal_request_body')
        self.assertTrue(isinstance(p, RequestBody))


class MutualReferenceTestCase(unittest.TestCase):
    """ test case for patching $ref against external
    document
    """

    @classmethod
    def setUpClass(kls):
        kls.app = SampleApp.create(
            url='file:///root/swagger.json',
            url_load_hook=gen_test_folder_hook(get_test_data_folder(version='2.0', which='ex')),
            to_spec_version='3.0.0'
        )

    def test_from_ex_back_to_root(self):
        """ make sure a $ref (to an object in root document)
        in external document can be patched
        """
        o, _ = self.app.resolve_obj(
            '#/definitions/s4',
            from_spec_version='2.0',
            to_spec_version='3.0.0'
        )

        # '#/definitions/s3' -> '#/components/schemas/s3'
        self.assertEqual(
            o.items.get_attrs('migration').ref_obj.items.ref,
            'file:///root/swagger.json#/components/schemas/s3'
        )

