from pyopenapi import App
from pyopenapi.primitives import Model
from ..utils import get_test_data_folder
import unittest
import json
import pytest
import sys


app = App._create_(get_test_data_folder(version='1.2', which='model_subtypes'))

u_mission = dict(id=1, username='mission', password='123123')
uwi_mary = dict(id=2, username='mary', password='456456', email='m@a.ry', phone='123')
uwi_kevin = dict(id=3, username='kevin')


class ModelInteritanceTestCase(unittest.TestCase):
    """ test cases for model inheritance """

    def test_inheritantce_full(self):
        """ init a Model with every property along
        the inheritance path.
        """
        _, resp = app.op['getUserByName'](username='mary')
        resp.apply_with(status=200, raw=json.dumps(uwi_mary), header={'Content-Type': 'application/json'})

        self.assertTrue(isinstance(resp.data, Model))
        m = resp.data
        self.assertEqual(m.id, 2)
        self.assertEqual(m.username, 'mary')
        self.assertEqual(m.email, 'm@a.ry')
        self.assertEqual(m.phone, '123')
        self.assertEqual(m.sub_type, 'UserWithInfo')

    def test_inheritance_partial(self):
        """ init a Model with only partial property
        set, expect failed.
        """
        _, resp = app.op['getUserByName'](username='kevin')

        resp.apply_with(status=200, raw=json.dumps(uwi_kevin), header={'Content-Type': 'application/json'})
        self.assertTrue(isinstance(resp.data, Model))
        m = resp.data
        self.assertEqual(m.id, 3)
        self.assertEqual(m.username, 'kevin')
        self.assertTrue('email' not in m)
        self.assertTrue('phone' not in m)
        self.assertEqual(m.sub_type, 'UserWithInfo')

    def test_inheritance_root(self):
        """ make sure we could init a root Model """
        req, _ = app.op['createUser'](body=u_mission)
        req.prepare()

        self.assertTrue(isinstance(req._p['body']['body'], Model))
        m = req._p['body']['body']
        self.assertEqual(m.id, 1)
        self.assertEqual(m.username, 'mission')
        self.assertEqual(m.sub_type, 'User')
        self.assertRaises(KeyError, getattr, m, 'email')
        self.assertRaises(KeyError, getattr, m, 'email')
