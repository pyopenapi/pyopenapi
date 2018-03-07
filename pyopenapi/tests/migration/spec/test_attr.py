from pyopenapi.migration.spec.attr import AttributeGroup, attr
import unittest


class GroupA(AttributeGroup):
        __attributes__ = {
            'a': dict(),
            'b': dict(default='bb'),
            'c': dict(key='cc'),
            'd': dict(builder=attr)
        }


class AttributeGroupTestCase(unittest.TestCase):
    """ test case for pyopenapi.migration.spec.AttributeGroup
    """

    def test_attribute_group(self):
        ag = GroupA({})

        # default behavior
        self.assertEqual(ag.a, None)
        ag.a = 1
        self.assertEqual(ag.a, 1)

        # with default
        self.assertEqual(ag.b, 'bb')
        ag.b = 2
        self.assertEqual(ag.b, 2)

        # key overwritten
        self.assertEqual(ag.c, None)
        ag.c = 3
        self.assertEqual(ag.c, 3)

        # specify 'builder'
        self.assertEqual(ag.d, None)
        ag.d = 4
        self.assertEqual(ag.d, 4)

    def test_attribute_group_with_init(self):
        """ make sure initial value is used
        """
        ag = GroupA({'a': 1, 'b': 2, 'cc': 3, 'd': 4})

        self.assertEqual(ag.a, 1)
        self.assertEqual(ag.b, 2)
        self.assertEqual(ag.c, 3)
        self.assertEqual(ag.d, 4)
