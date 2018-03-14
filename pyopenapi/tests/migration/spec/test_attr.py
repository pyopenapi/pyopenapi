# pylint: disable=attribute-defined-outside-init

import unittest

from pyopenapi.migration.spec.attr import AttributeGroup, attr


# pylint: disable=invalid-name
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
        group_a = GroupA({})

        # default behavior
        self.assertEqual(group_a.a, None)
        group_a.a = 1
        self.assertEqual(group_a.a, 1)

        # with default
        self.assertEqual(group_a.b, 'bb')
        group_a.b = 2
        self.assertEqual(group_a.b, 2)

        # key overwritten
        self.assertEqual(group_a.c, None)
        group_a.c = 3
        self.assertEqual(group_a.c, 3)

        # specify 'builder'
        self.assertEqual(group_a.d, None)
        group_a.d = 4
        self.assertEqual(group_a.d, 4)

    def test_attribute_group_with_init(self):
        """ make sure initial value is used
        """
        group_a = GroupA({'a': 1, 'b': 2, 'cc': 3, 'd': 4})

        self.assertEqual(group_a.a, 1)
        self.assertEqual(group_a.b, 2)
        self.assertEqual(group_a.c, 3)
        self.assertEqual(group_a.d, 4)
