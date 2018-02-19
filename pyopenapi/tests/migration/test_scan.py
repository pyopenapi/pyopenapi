from pyopenapi.contrib.pyswagger.core import App
from pyopenapi.migration.scan import Scanner, Scanner2, Dispatcher
from pyopenapi.migration.versions.v1_2.objects import (
    ApiDeclaration,
    Authorization,
    Operation,
    ResponseMessage,
    Parameter
)
from pyopenapi.migration.versions.v3_0_0.objects import (
    Header as Header3,
    Parameter as Parameter3,
)
from ..utils import get_test_data_folder
import unittest
import weakref


class CountObject(object):
    """ a scanner for counting objects and looking for
    longest attribute name. Just for test.
    """
    class Disp(Dispatcher): pass

    def __init__(self):
        self.total = {
            ApiDeclaration: 0,
            Authorization: 0,
            Operation: 0,
            ResponseMessage: 0
        }
        self.long_name = ''

    @Disp.register([ApiDeclaration, Authorization, Operation, ResponseMessage])
    def _count(self, path, obj, _):
        self.total[obj.__class__] = self.total[obj.__class__] + 1
        return path

    @Disp.result
    def _result(self, name):
        if len(name) > len(self.long_name):
            self.long_name = name


class PathRecord(object):
    """ a scanner to record all json path
    """

    class Disp(Dispatcher): pass

    def __init__(self):
        self.api_declaration = []
        self.authorization = []
        self.response_message = []
        self.parameter = []

    @Disp.register([ApiDeclaration])
    def _api_declaration(self, path, obj, _):
        self.api_declaration.append(path)

    @Disp.register([Authorization])
    def _authorization(self, path, obj, _):
        self.authorization.append(path)

    @Disp.register([ResponseMessage])
    def _response_message(self, path, obj, _):
        self.response_message.append(path)

    @Disp.register([Parameter])
    def _parameter(self, path, obj, _):
        self.parameter.append(path)


app = App.load(get_test_data_folder(version='1.2', which='wordnik'))


class ScannerTestCase(unittest.TestCase):
    """ test scanner """
    def test_count(self):
        s = Scanner(app)
        co = CountObject()
        s.scan(route=[co], root=app.raw)
        for name in app.raw.cached_apis:
            s.scan(route=[co], root=app.raw.cached_apis[name])

        self.assertEqual(co.long_name, '#/apis/3/operations/0/responseMessages/0')
        self.assertEqual(co.total, {
            Authorization: 1,
            ApiDeclaration: 3,
            Operation: 20,
            ResponseMessage: 23
        })

    def test_leaves(self):
        s = Scanner(app)
        co = CountObject()
        s.scan(route=[co], root=app.raw, leaves=[Operation])
        for name in app.raw.cached_apis:
            s.scan(route=[co], root=app.raw.cached_apis[name], leaves=[Operation])

        # the scanning would stop at Operation, so ResponseMessage
        # would not be counted.
        self.assertEqual(co.total, {
            Authorization: 1,
            ApiDeclaration: 3,
            Operation: 20,
            ResponseMessage: 0
        })


    def test_path(self):
        self.maxDiff = None
        s = Scanner(app)
        p = PathRecord()
        s.scan(route=[p], root=app.raw)
        s.scan(route=[p], root=app.raw.cached_apis['store'])

        self.assertEqual(sorted(p.api_declaration), sorted(['#']))
        self.assertEqual(p.authorization, ['#/authorizations/oauth2'])
        self.assertEqual(sorted(p.response_message), sorted([
            '#/apis/0/operations/0/responseMessages/0',
            '#/apis/1/operations/0/responseMessages/1',
            '#/apis/1/operations/0/responseMessages/0',
            '#/apis/1/operations/1/responseMessages/1',
            '#/apis/1/operations/1/responseMessages/0'
        ]))
        self.assertEqual(sorted(p.parameter), sorted([
            '#/apis/0/operations/0/parameters/0',
            '#/apis/1/operations/0/parameters/0',
            '#/apis/1/operations/1/parameters/0',
        ]))


class ResolveTestCase(unittest.TestCase):
    """ test for scanner: Resolve """

    @classmethod
    def setUpClass(kls):
        kls.app = App._create_(get_test_data_folder(version='1.2', which='model_subtypes'))

    def test_ref_resolve(self):
        """ make sure pre resolve works """
        ref = getattr(self.app.resolve('#/components/schemas/user!##!UserWithInfo').allOf[0], 'ref_obj')
        self.assertTrue(isinstance(ref, weakref.ProxyTypes))
        self.assertEqual(ref, self.app.resolve('#/components/schemas/user!##!User'))


class CountParemeter3(object):
    """ a scanner just for test
    """
    class Disp(Dispatcher): pass

    def __init__(self):
        self.total = {
            Header3: 0,
            Parameter3: 0,
        }

    @Disp.register([Header3, Parameter3])
    def _count(self, path, obj):
        self.total[obj.__class__] = self.total[obj.__class__] + 1


class Scanner2TestCase(unittest.TestCase):
    """ test case for Scanner2 """

    def test_child_class_called_twice(self):
        """ make a callback for 'Header' and 'Parameter' would only be called once,
        when Header inherit Paremeter
        """
        header = Header3({})
        cp = CountParemeter3()
        Scanner2().scan(route=[cp], root=header)

        self.assertEqual(cp.total[Header3], 1)
        self.assertEqual(cp.total[Parameter3], 0)

