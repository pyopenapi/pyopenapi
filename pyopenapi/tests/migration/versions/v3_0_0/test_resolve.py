# -*- coding: utf-8 -*-
import unittest

from pyopenapi.utils import jr_split, normalize_url
from pyopenapi.migration.versions.v3_0_0.objects import (
    Reference,
    Schema,
    Parameter,
    Header,
    RequestBody,
    Response,
    Link,
    Callback,
    PathItem,
    Operation,
    SecurityScheme,
)
from ....utils import get_test_data_folder, gen_test_folder_hook, SampleApp


class PathItemMergeTestCase(unittest.TestCase):
    """ test case for merging external path item """

    @classmethod
    def setUpClass(cls):
        cls.app = SampleApp.create(
            url='file:///root.yml',
            url_load_hook=gen_test_folder_hook(
                get_test_data_folder(version='3.0.0', which='external')),
            to_spec_version='3.0.0')

    def test_merge_basic(self):
        """ one path item in root ref to an external path item
        """
        path_item, _ = self.app.resolve_obj(
            '#/paths/~1test1',
            from_spec_version='3.0.0',
        )

        def _not_exist(obj):
            self.assertEqual(obj.delete, None)
            self.assertEqual(obj.options, None)
            self.assertEqual(obj.head, None)
            self.assertEqual(obj.patch, None)
            self.assertEqual(obj.trace, None)

        # check original object is not touch, or 'dump' would be wrong
        _not_exist(path_item)
        self.assertNotEqual(path_item.post, None)

        another, _ = self.app.resolve_obj(
            'file:///partial_path_item_1.yml#/test1',
            parser=PathItem,
            from_spec_version='3.0.0',
        )
        self.assertNotEqual(another.get, None)
        self.assertNotEqual(another.put, None)

        final = path_item.get_attrs('migration').final_obj
        _not_exist(final)
        self.assertNotEqual(final.get, None)
        self.assertNotEqual(final.post, None)
        # children objects are shared
        self.assertEqual(id(path_item.post), id(final.post))
        self.assertEqual(id(another.get), id(final.get))
        self.assertEqual(id(another.put), id(final.put))

    def test_merge_cascade(self):
        """ path item in root ref to an external path item with
        ref to yet another path item, too
        """

        path_item, _ = self.app.resolve_obj(
            '#/paths/~1test2',
            from_spec_version='3.0.0',
        )

        def _not_exist(obj):
            self.assertEqual(obj.put, None)
            self.assertEqual(obj.delete, None)
            self.assertEqual(obj.options, None)
            self.assertEqual(obj.head, None)
            self.assertEqual(obj.patch, None)
            self.assertEqual(obj.trace, None)

        _not_exist(path_item)
        self.assertEqual(path_item.get, None)
        self.assertEqual(path_item.post, None)

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

        final = path_item.get_attrs('migration').final_obj
        _not_exist(final)
        self.assertNotEqual(final.get, None)
        self.assertNotEqual(final.post, None)
        self.assertEqual(id(final.get), id(another_1.get))
        self.assertEqual(id(final.post), id(another_2.post))

    def test_path_item_no_ref(self):
        """ path item object without $ref
        should not have 'final_obj' property
        """
        path_item, _ = self.app.resolve_obj(
            'file:///partial_path_item_2.yml#/test2',
            from_spec_version='3.0.0',
        )
        self.assertEqual(path_item.get_attrs('migration').final_obj, None)

    def test_path_item_parameters(self):
        """ make sure parameters in path-item are handled
        """
        test4, _ = self.app.resolve_obj(
            '#/paths/~1test4',
            from_spec_version='3.0.0',
        )

        param = test4.parameters[0]
        self.assertTrue(isinstance(param, Reference))
        self.assertNotEqual(param.get_attrs('migration').ref_obj, None)

        param = test4.parameters[1]
        self.assertTrue(isinstance(param, Reference))
        self.assertNotEqual(param.get_attrs('migration').ref_obj, None)


class ResolveTestCase(unittest.TestCase):
    """ test cases related to 'resolving' stuffs
    """

    @classmethod
    def setUpClass(cls):
        cls.app = SampleApp.create(
            url='file:///root.yml',
            url_load_hook=gen_test_folder_hook(
                get_test_data_folder(version='3.0.0', which='external')),
            to_spec_version='3.0.0')

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
            'file:///root.yml#/components/responses/void')

    def test_resolve_schema(self):
        """ make sure 'Schema' is resolved and cached
        """
        schema, _ = self.app.resolve_obj(
            '#/components/schemas/partial_1',
            from_spec_version='3.0.0',
        )
        self.assertTrue(isinstance(schema, Reference))
        self.assertEqual(
            schema.get_attrs('migration').normalized_ref,
            'file:///partial_1.yml#/schemas/partial_1')
        self.assertTrue(
            isinstance(schema.get_attrs('migration').ref_obj, Schema))
        self.assertEqual(schema.get_attrs('migration').ref_obj.type_, 'string')

    def test_resolve_parameter(self):
        """ make sure 'Parameter' is resolved and cached
        """
        param, _ = self.app.resolve_obj(
            '#/paths/~1test3/get/parameters/0',
            from_spec_version='3.0.0',
        )
        self.assertEqual(
            param.get_attrs('migration').normalized_ref,
            'file:///root.yml#/components/parameters/test3.p1')
        self.assertTrue(
            isinstance(param.get_attrs('migration').ref_obj, Reference))

        param = param.get_attrs('migration').ref_obj
        self.assertEqual(
            param.get_attrs('migration').normalized_ref,
            'file:///partial_1.yml#/parameters/test3.p1')
        self.assertTrue(
            isinstance(param.get_attrs('migration').ref_obj, Parameter))

        param = param.get_attrs('migration').ref_obj
        self.assertEqual(param.in_, 'query')

        schema = param.schema
        self.assertTrue(isinstance(schema, Reference))
        self.assertEqual(
            schema.get_attrs('migration').normalized_ref,
            'file:///partial_2.yml#/schemas/test3.p1.schema')

        schema = schema.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(schema, Schema))
        self.assertEqual(schema.type_, 'string')
        self.assertEqual(schema.format_, 'password')

    def test_resolve_header(self):
        """ make sure 'Header' is resolved and cached
        """
        param, _ = self.app.resolve_obj(
            '#/paths/~1test3/delete/parameters/0',
            from_spec_version='3.0.0',
        )
        self.assertTrue(isinstance(param, Reference))
        self.assertEqual(
            param.get_attrs('migration').normalized_ref,
            'file:///root.yml#/components/headers/test3.header.1')

        param = param.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(param, Reference))
        self.assertEqual(
            param.get_attrs('migration').normalized_ref,
            'file:///partial_1.yml#/headers/test3.header.1')

        header = param.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(header, Header))
        self.assertEqual(header.in_, 'header')
        self.assertEqual(header.name, None)
        self.assertTrue(isinstance(header.schema, Reference))
        self.assertEqual(
            header.schema.get_attrs('migration').normalized_ref,
            'file:///partial_2.yml#/schemas/test3.header.1.schema')

        schema = header.schema.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(schema, Schema))
        self.assertEqual(schema.type_, 'integer')
        self.assertEqual(schema.format_, 'int32')

    def test_resolve_request_body(self):
        """ make sure 'RequestBody' is resolved and cached
        """
        body, _ = self.app.resolve_obj(
            '#/paths/~1test3/post/requestBody',
            from_spec_version='3.0.0',
        )
        self.assertTrue(isinstance(body, Reference))
        self.assertEqual(
            body.get_attrs('migration').normalized_ref,
            'file:///root.yml#/components/requestBodies/test3.body.1')

        body = body.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(body, Reference))
        self.assertEqual(
            body.get_attrs('migration').normalized_ref,
            'file:///partial_1.yml#/bodies/test3.body.1')

        body = body.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(body, RequestBody))
        self.assertTrue('application/json' in body.content)

        schema = body.content['application/json'].schema
        self.assertTrue(isinstance(schema, Reference))
        self.assertEqual(
            schema.get_attrs('migration').normalized_ref,
            'file:///root.yml#/components/schemas/test3.body.1.schema.1')

        schema = schema.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(schema, Reference))
        self.assertEqual(
            schema.get_attrs('migration').normalized_ref,
            'file:///partial_2.yml#/schemas/test3.body.1.schema.1')

        schema = schema.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(schema, Schema))
        self.assertEqual(schema.type_, 'object')
        self.assertTrue('email' in schema.properties)
        self.assertEqual(schema.properties['email'].type_, 'string')
        self.assertTrue('password' in schema.properties)
        self.assertEqual(schema.properties['password'].type_, 'string')
        self.assertEqual(schema.properties['password'].format_, 'password')

    def test_resolve_response(self):
        """ make sure 'Response' is resolved and cached
        """
        resp, _ = self.app.resolve_obj(
            '#/paths/~1test3/get/responses/400',
            from_spec_version='3.0.0',
        )
        self.assertTrue(isinstance(resp, Reference))
        self.assertEqual(
            resp.get_attrs('migration').normalized_ref,
            'file:///root.yml#/components/responses/BadRequest')

        resp = resp.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(resp, Reference))
        self.assertEqual(
            resp.get_attrs('migration').normalized_ref,
            'file:///partial_1.yml#/responses/test3.get.response.400')

        resp = resp.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(resp, Response))
        self.assertEqual(resp.description, 'test description')
        self.assertTrue('test-x-device-id' in resp.headers)
        self.assertTrue('some-link' in resp.links)

        header = resp.headers['test-x-device-id']
        self.assertTrue(isinstance(header, Reference))
        header = header.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(header, Header))
        self.assertEqual(header.schema.type_, 'string')

        link_ = resp.links['some-link']
        self.assertTrue(isinstance(link_, Reference))
        link_ = link_.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(link_, Link))
        self.assertEqual(link_.operation_ref,
                         'file:///root.yml#/paths/~1test1/post')
        self.assertTrue('id_1' in link_.parameters)
        self.assertEqual(link_.parameters['id_1'], '$response.body#/id_1')

    def test_resolve_callback(self):
        """ make sure 'Callback' in components is resolved and cached
        """
        callback, _ = self.app.resolve_obj(
            '#/components/callbacks/cb.1',
            from_spec_version='3.0.0',
        )
        self.assertTrue(isinstance(callback, Reference))
        self.assertEqual(
            callback.get_attrs('migration').normalized_ref,
            'file:///partial_1.yml#/callbacks/cb.1')

        callback = callback.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(callback, Callback))
        self.assertEqual(callback['/test-cb-1'].summary,
                         'some test path item for callback')

        path_item = callback['/test-cb-1'].get
        self.assertEqual(path_item.operation_id, 'cb.1.get')
        param = path_item.parameters[0]
        self.assertEqual(param.name, 'cb.1.p.1')
        self.assertEqual(param.in_, 'query')
        self.assertEqual(param.schema.type_, 'string')

        resp = path_item.responses['default']
        self.assertTrue(isinstance(resp, Reference))
        self.assertEqual(
            resp.get_attrs('migration').normalized_ref,
            'file:///root.yml#/components/responses/void')

        resp = resp.get_attrs('migration').ref_obj
        self.assertTrue(isinstance(resp, Response))
        self.assertEqual(resp.description, 'void response')

        # able to resolve PathItem under callback
        path_item, _ = self.app.resolve_obj(
            'file:///partial_1.yml#/callbacks/cb.1/~1test-cb-1',
            from_spec_version='3.0.0',
        )
        self.assertTrue(isinstance(path_item, PathItem))


class ResolveWithObjectRelocationTestCase(unittest.TestCase):
    """ test case for App.resolve with object relocation
    """

    @classmethod
    def setUpClass(cls):
        doc_path = get_test_data_folder(
            version='2.0',
            which='upgrade',
        )

        cls.app = SampleApp.create(doc_path, to_spec_version='3.0.0')
        cls.doc_path = normalize_url(doc_path)

    def test_operation(self):
        """ operation should not be changed
        """
        jref = '#/paths/~1p1/get'
        operation, new_ref = self.app.resolve_obj(
            jref, from_spec_version='2.0', to_spec_version='3.0.0')
        url, jp = jr_split(new_ref)
        self.assertEqual(jp, jref)
        self.assertEqual(url, self.doc_path)
        self.assertTrue(isinstance(operation, Operation))

    def test_parameter(self):
        """ parameters -> components/parameters
        """
        param, new_ref = self.app.resolve_obj(
            '#/parameters/query_string',
            from_spec_version='2.0',
            to_spec_version='3.0.0')
        url, jp = jr_split(new_ref)
        self.assertEqual(url, self.doc_path)
        self.assertEqual(jp, '#/components/parameters/query_string')
        self.assertTrue(isinstance(param, Parameter))

    def test_body_parameter(self):
        """ parameters -> components/requestBodies
        """
        body, new_ref = self.app.resolve_obj(
            '#/parameters/body_file_ref',
            from_spec_version='2.0',
            to_spec_version='3.0.0')
        url, jp = jr_split(new_ref)
        self.assertEqual(url, self.doc_path)
        self.assertEqual(jp, '#/components/requestBodies/body_file_ref')
        self.assertTrue(isinstance(body, RequestBody))

    def test_form_parameter(self):
        """ parameters -> components/requestBodies
        """
        param, new_ref = self.app.resolve_obj(
            '#/parameters/form_string',
            from_spec_version='2.0',
            to_spec_version='3.0.0')
        url, jp = jr_split(new_ref)
        self.assertEqual(url, self.doc_path)
        self.assertEqual(jp, '#/components/requestBodies/form_string')
        self.assertTrue(isinstance(param, RequestBody))

    def test_response(self):
        """ responses -> components/responses
        """
        void_, new_ref = self.app.resolve_obj(
            '#/responses/void',
            from_spec_version='2.0',
            to_spec_version='3.0.0')
        url, jp = jr_split(new_ref)
        self.assertEqual(url, self.doc_path)
        self.assertEqual(jp, '#/components/responses/void')
        self.assertTrue(isinstance(void_, Response))

    def test_definitions(self):
        """ definitions -> components/schemas
        """
        schema, new_ref = self.app.resolve_obj(
            '#/definitions/category',
            from_spec_version='2.0',
            to_spec_version='3.0.0')
        url, jp = jr_split(new_ref)
        self.assertEqual(url, self.doc_path)
        self.assertEqual(jp, '#/components/schemas/category')
        self.assertTrue(isinstance(schema, Schema))

    def test_security_definitions(self):
        """ securityDefinitions -> components/securitySchemes
        """
        sec, new_ref = self.app.resolve_obj(
            '#/securityDefinitions/petstore_auth',
            from_spec_version='2.0',
            to_spec_version='3.0.0')
        url, jp = jr_split(new_ref)
        self.assertEqual(url, self.doc_path)
        self.assertEqual(jp, '#/components/securitySchemes/petstore_auth')
        self.assertTrue(isinstance(sec, SecurityScheme))

    def test_path_item_body_parameters(self):
        """ body paraemter under 'PathItem' object
        should support object relocation, too
        """
        param, new_ref = self.app.resolve_obj(
            '#/paths/~1p3~1{user_name}/parameters/0',
            from_spec_version='2.0',
            to_spec_version='3.0.0')
        url, jp = jr_split(new_ref)
        self.assertEqual(url, self.doc_path)
        self.assertEqual(
            jp, '#/paths/~1p3~1{user_name}/x-pyopenapi_internal_request_body')
        self.assertTrue(isinstance(param, RequestBody))


class MutualReferenceTestCase(unittest.TestCase):
    """ test case for patching $ref against external
    document
    """

    @classmethod
    def setUpClass(cls):
        cls.app = SampleApp.create(
            url='file:///root/swagger.json',
            url_load_hook=gen_test_folder_hook(
                get_test_data_folder(version='2.0', which='ex')),
            to_spec_version='3.0.0')

    def test_from_ex_back_to_root(self):
        """ make sure a $ref (to an object in root document)
        in external document can be patched
        """
        schema, _ = self.app.resolve_obj(
            '#/definitions/s4',
            from_spec_version='2.0',
            to_spec_version='3.0.0')

        # '#/definitions/s3' -> '#/components/schemas/s3'
        self.assertEqual(
            schema.items.get_attrs('migration').ref_obj.items.ref,
            'file:///root/swagger.json#/components/schemas/s3')
