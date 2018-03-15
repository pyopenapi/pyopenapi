# -*- coding: utf-8 -*-
# pylint: disable=no-member,invalid-name,attribute-defined-outside-init

import unittest

from pyopenapi.migration.spec import (
    Base2,
    field,
    child,
    rename,
    map_,
    list_,
    _Map,
    _List,
)
from pyopenapi.migration.spec.attr import AttributeGroup


class BObj(Base2):
    __fields__ = {
        'bb': dict(builder=field),
    }


class AObj(Base2):
    __fields__ = {
        'a': dict(builder=field),
        'b': dict(builder=field, required=True),
        'd': dict(readonly=False),
    }

    __internal__ = {
        'internal_c': dict(),
        'd3_renamed': dict(key='a', builder=rename),
        'd4_renamed': dict(key='d', builder=rename),
    }

    __children__ = {
        'c': dict(child_builder=BObj),
    }


class CObj(Base2):
    __children__ = {
        'cc': dict(child_builder=map_(AObj)),
        'ccc': dict(child_builder=list_(AObj)),
    }


class DObj(Base2):
    __children__ = {
        'd1': dict(child_builder=map_(list_(AObj))),
        'd2': dict(child_builder=list_(map_(AObj))),
        'd3': dict(child_builder=map_(map_(AObj))),
    }


def if_not_a(obj_class):
    def func(spec, path=None, override=None):
        if 'a' in spec:
            return AObj(spec, path=path, override=override)
        return obj_class(spec, path=path, override=override)

    func.__name__ = 'if_not_a_or_' + obj_class.__name__
    return func


class EObj(Base2):
    __children__ = {
        'e1': dict(child_builder=list_(if_not_a(BObj))),
        'e2': dict(child_builder=if_not_a(map_(map_(AObj)))),
        'e3': dict(child_builder=if_not_a(DObj)),
        'e4': dict(child_builder=if_not_a(map_(AObj))),
    }


class FObj(AObj):
    __fields__ = {
        'f1': dict(builder=field),
    }


class GObj(Base2):
    __children__ = {
        'a': dict(child_builder=BObj),
        'b': dict(child_builder=BObj),
        'c': dict(child_builder=BObj),
    }


class HObj(Base2):
    __fields__ = {
        'a': dict(builder=field, key='b'),
    }


class IObj(AObj):
    __fields__ = {
        'a': dict(key='cc', builder=field),
    }


class JObj(Base2):
    __fields__ = {
        'a': dict(builder=field, restricted=True),
        'b': dict(builder=field, restricted=True, default='hi'),
    }


# pylint: disable=unused-argument
def is_str(spec, path, override):
    return spec


class KObj(Base2):
    __fields__ = {
        'a': dict(builder=field),
    }

    __children__ = {
        'b': dict(child_builder=list_(is_str)),
        'c': dict(child_builder=map_(is_str))
    }


KObj.attach_field('k1', builder=child, child_builder=KObj)


class BGroup(AttributeGroup):
    __attributes__ = {
        'a': dict(),
    }


class Base2TestCase(unittest.TestCase):
    """ test case for base2.py """

    def test_field_meta(self):
        """ check FieldMeta
        """
        # should fill __child__ with fields created by builder:child
        self.assertEqual(list(AObj.__children__.keys()), ['c'])

    def test_field(self):
        """ make sure builder:field works
        """
        # default value is None
        self.assertEqual(AObj({}).a, None)
        self.assertEqual(AObj({'a': 1}).a, 1)

        # when required, raise exception when none
        self.assertRaises(Exception, lambda: AObj({}).b)
        self.assertEqual(AObj({'b': 2}).b, 2)

    def test_internal(self):
        """ make sure builder:internal works
        """
        obj = AObj({'a': 1, 'b': 2, 'ic': 3})
        self.assertEqual(sorted(obj.get_field_names()),
                         ['a', 'b', 'c', 'd'
                          ])  # internal is not included in 'get_field_names()'
        self.assertEqual(
            obj.internal_c,
            None)  # internal is separated from input spec (in __fields__)

        obj.internal_c = 4
        self.assertEqual(obj.internal_c, 4)

        # make sure we won't dump internal fields
        self.assertEqual(obj.dump(), {'a': 1, 'b': 2})

    def test_child(self):
        """ make sure builder:child works
        """
        # default is None
        self.assertEqual(AObj({}).c, None)
        self.assertNotEqual(AObj({'c': {}}).c, None)
        # child's field also created
        self.assertEqual(AObj({'c': {'bb': 3}}).c.bb, 3)

    def test_map(self):
        """ make sure container:Map works
        """
        obj = CObj({'cc': {'key1': {'a': 1}, 'key2': {'b': 2}}})
        self.assertTrue(issubclass(obj.cc.__class__, _Map))
        self.assertTrue('key1' in obj.cc)
        self.assertTrue(isinstance(obj.cc['key1'], AObj))
        self.assertTrue('key2' in obj.cc)
        self.assertTrue(isinstance(obj.cc['key2'], AObj))
        self.assertEqual(obj.cc['key1'].a, 1)
        self.assertEqual(obj.cc['key2'].b, 2)

        for k, val in obj.cc.items():
            if k == 'key1':
                self.assertEqual({'a': 1}, val.dump())
                break
        else:
            self.fail('"key1" not found')

    def test_list(self):
        """ make sure container:List works
        """
        obj = CObj({'ccc': [{'a': 1}, {'a': 2}]})
        self.assertTrue(issubclass(obj.ccc.__class__, _List))
        cnts = {1: 0, 2: 0}
        for e in obj.ccc:
            cnts[e.a] += 1
        for idx in cnts:
            self.assertEqual(cnts[idx], 1)

    def test_composite_container(self):
        """ check child_builder=List(Map(List ....)
        """
        # map of list
        obj = DObj({
            'd1': {
                'key1': [{
                    'a': 1
                }, {
                    'a': 2
                }],
                'key2': [{
                    'a': 3
                }, {
                    'a': 4
                }]
            }
        })
        self.assertEqual(obj.d1['key1'][0].a, 1)
        self.assertEqual(obj.d1['key1'][1].a, 2)
        self.assertEqual(obj.d1['key2'][0].a, 3)
        self.assertEqual(obj.d1['key2'][1].a, 4)

        # list of map
        obj = DObj({
            'd2': [{
                'key1': {
                    'a': 1
                },
                'key2': {
                    'a': 2
                }
            }, {
                'key3': {
                    'a': 3
                },
                'key4': {
                    'a': 4
                }
            }]
        })
        self.assertEqual(obj.d2[0]['key1'].a, 1)
        self.assertEqual(obj.d2[0]['key2'].a, 2)
        self.assertEqual(obj.d2[1]['key3'].a, 3)
        self.assertEqual(obj.d2[1]['key4'].a, 4)

        # map of map
        obj = DObj({
            'd3': {
                'key1': {
                    'key11': {
                        'a': 1
                    },
                    'key12': {
                        'a': 2
                    }
                },
                'key2': {
                    'key21': {
                        'a': 3
                    },
                    'key22': {
                        'a': 4
                    }
                }
            }
        })
        self.assertEqual(obj.d3['key1']['key11'].a, 1)
        self.assertEqual(obj.d3['key1']['key12'].a, 2)
        self.assertEqual(obj.d3['key2']['key21'].a, 3)
        self.assertEqual(obj.d3['key2']['key22'].a, 4)

    def test_if_not_ref(self):
        """ make sure we can write a function as a selector to return expected type
        ex. Reference Object in OpenAPI 3.0 -> Some Object | Reference Object
        """
        obj = EObj({'e1': [{'a': 1}, {'bb': 2}]})
        self.assertTrue(isinstance(obj.e1[0], AObj))
        self.assertEqual(obj.e1[0].a, 1)
        self.assertTrue(isinstance(obj.e1[1], BObj))
        self.assertEqual(obj.e1[1].bb, 2)

        # the case for Reference Object | Callbacs Object
        obj = EObj({'e2': {'a': 1}})
        self.assertTrue(isinstance(obj.e2, AObj))
        self.assertEqual(obj.e2.a, 1)
        obj = EObj({
            'e2': {
                'key1': {
                    'key11': {
                        'a': 1
                    }
                },
                'key2': {
                    'key21': {
                        'a': 2
                    }
                }
            }
        })
        self.assertFalse(isinstance(obj.e2, AObj))
        self.assertEqual(obj.e2['key1']['key11'].a, 1)
        self.assertEqual(obj.e2['key2']['key21'].a, 2)

        # func as child_builder
        obj = EObj({'e3': {'a': 1}})
        self.assertTrue(isinstance(obj.e3, AObj))
        self.assertEqual(obj.e3.a, 1)
        self.assertTrue(isinstance(EObj({'e3': {}}).e3, DObj))

        # funct with container
        obj = EObj({'e4': {'a': 1}})
        self.assertTrue(isinstance(obj.e4, AObj))
        self.assertEqual(obj.e4.a, 1)
        obj = EObj({'e4': {'key1': {'a': 1}, 'key2': {'a': 2}}})
        self.assertEqual(obj.e4['key1'].a, 1)
        self.assertEqual(obj.e4['key2'].a, 2)

    def test_inheritance(self):
        """ inheritance
        """
        # both fields are created
        obj = FObj({'a': 1, 'b': 2, 'f1': 3})
        self.assertEqual(obj.a, 1)
        self.assertEqual(obj.b, 2)
        self.assertEqual(obj.f1, 3)

    def test_compare(self):
        """ Base2Obj.compare
        """
        # when a field is different
        obj_1 = AObj({'a': 1, 'b': 1})
        obj_2 = AObj({'a': 2, 'b': 1})
        self.assertEqual(obj_1.compare(obj_2), (False, 'a'))

        # child field, missing, or different
        obj_1 = AObj({'b': 1, 'c': {'bb': 1}})
        obj_2 = AObj({'b': 1})

        self.assertEqual(obj_1.compare(obj_2), (False, 'c'))
        obj_3 = AObj({'b': 1, 'c': {'bb': 2}})
        self.assertEqual(obj_1.compare(obj_3), (False, 'c/bb'))

        # _Map
        obj_1 = CObj({
            'cc': {
                'key1': {
                    'a': 1,
                    'b': 1
                },
                'key2': {
                    'a': 1,
                    'b': 2
                }
            }
        })
        obj_2 = CObj({
            'cc': {
                'key1': {
                    'a': 1,
                    'b': 1
                },
                'key2': {
                    'a': 1,
                    'b': 3
                }
            }
        })
        self.assertEqual(obj_1.compare(obj_2), (False, 'cc/key2/b'))

        # _List
        obj_1 = CObj({'ccc': [{'a': 1, 'b': 2}, {'a': 2, 'b': 3}]})
        obj_2 = CObj({'ccc': [{'a': 1, 'b': 2}, {'a': 3, 'b': 3}]})
        self.assertEqual(obj_1.compare(obj_2), (False, 'ccc/1/a'))
        self.assertEqual(obj_1.compare(obj_1), (True, ''))
        self.assertEqual(obj_2.compare(obj_2), (True, ''))

        # _Map of _List
        obj_1 = DObj({
            'd1': {
                'key1': [{
                    'b': 1
                }, {
                    'b': 2
                }],
                'key2': [{
                    'b': 3
                }, {
                    'b': 4
                }]
            }
        })
        obj_2 = DObj({
            'd1': {
                'key1': [{
                    'b': 1
                }, {
                    'b': 3
                }],
                'key2': [{
                    'b': 3
                }, {
                    'b': 4
                }]
            }
        })
        obj_3 = DObj({'d1': {'key1': [{'b': 1}, {'b': 2}]}})
        self.assertEqual(obj_1.compare(obj_2), (False, 'd1/key1/1/b'))
        self.assertEqual(obj_1.compare(obj_3), (False, 'd1/key2'))
        self.assertEqual(obj_1.compare(obj_1), (True, ''))
        self.assertEqual(obj_2.compare(obj_2), (True, ''))
        self.assertEqual(obj_3.compare(obj_3), (True, ''))

        # _List of _Map
        obj_1 = DObj({
            'd2': [{
                'key1': {
                    'b': 1
                },
                'key2': {
                    'b': 2
                }
            }, {
                'key3': {
                    'b': 3
                },
                'key4': {
                    'b': 4
                }
            }]
        })
        obj_2 = DObj({
            'd2': [{
                'key1': {
                    'b': 1
                },
                'key2': {
                    'b': 2
                }
            }, {
                'key3': {
                    'b': 3
                },
                'key4': {
                    'b': 5
                }
            }]
        })
        obj_3 = DObj({
            'd2': [{
                'key1': {
                    'b': 1
                }
            }, {
                'key3': {
                    'b': 3
                },
                'key4': {
                    'b': 4
                }
            }]
        })
        self.assertEqual(obj_1.compare(obj_2), (False, 'd2/1/key4/b'))
        self.assertEqual(obj_1.compare(obj_3), (False, 'd2/0/key2'))
        self.assertEqual(obj_1.compare(obj_1), (True, ''))
        self.assertEqual(obj_2.compare(obj_2), (True, ''))
        self.assertEqual(obj_3.compare(obj_3), (True, ''))

        # _Map of _Map
        obj_1 = DObj({
            'd3': {
                'key1': {
                    'key11': {
                        'b': 1
                    },
                    'key12': {
                        'b': 2
                    }
                },
                'key2': {
                    'key21': {
                        'b': 3
                    },
                    'key22': {
                        'b': 4
                    }
                }
            }
        })
        obj_2 = DObj({
            'd3': {
                'key1': {
                    'key11': {
                        'b': 1
                    },
                    'key12': {
                        'b': 2
                    }
                },
                'key2': {
                    'key21': {
                        'b': 3
                    },
                    'key22': {
                        'b': 5
                    }
                }
            }
        })
        obj_3 = DObj({
            'd3': {
                'key1': {
                    'key11': {
                        'b': 1
                    },
                    'key12': {
                        'b': 2
                    }
                },
                'key2': {
                    'key21': {
                        'b': 3
                    }
                }
            }
        })
        self.assertEqual(obj_1.compare(obj_2), (False, 'd3/key2/key22/b'))
        self.assertEqual(obj_1.compare(obj_3), (False, 'd3/key2/key22'))
        self.assertEqual(obj_1.compare(obj_1), (True, ''))
        self.assertEqual(obj_2.compare(obj_2), (True, ''))
        self.assertEqual(obj_3.compare(obj_3), (True, ''))

        # dict
        obj_1 = AObj({'b': {'a': 1, 'b': 2}})
        obj_2 = AObj({'b': {'a': 2, 'b': 2}})
        obj_3 = AObj({'b': {'a': 1}})
        self.assertEqual(obj_1.compare(obj_2), (False, 'b/a'))
        self.assertEqual(obj_1.compare(obj_3), (False, 'b/b'))
        self.assertEqual(obj_1.compare(obj_1), (True, ''))
        self.assertEqual(obj_2.compare(obj_2), (True, ''))
        self.assertEqual(obj_3.compare(obj_3), (True, ''))

        # list
        obj_1 = AObj({'b': [1, 2, 3]})
        obj_2 = AObj({'b': [1, 2, 4]})
        self.assertEqual(obj_1.compare(obj_2), (False, 'b/2'))
        self.assertEqual(obj_1.compare(obj_1), (True, ''))
        self.assertEqual(obj_2.compare(obj_2), (True, ''))

    def test_attach_child(self):
        """ Base2Obj.attach_child
        """
        obj = AObj({})
        obj.attach_child('c', BObj({'bb': 1}))
        self.assertEqual(obj.c.bb, 1)

    def test_dump(self):
        """ [Base2Obj, _Map, _List].dump
        """
        spec = {'b': 1}
        obj = AObj(spec)
        self.assertEqual(obj.dump(), spec)

        spec = {'b': 1, 'c': {'bb': 2}}
        obj = AObj(spec)
        self.assertEqual(obj.dump(), spec)
        # children first
        obj.attach_child('c', BObj({'bb': 3}))
        self.assertEqual(obj.dump(), {'b': 1, 'c': {'bb': 3}})

        # _Map
        spec = {'cc': {'key1': {'b': 1}, 'key2': {'b': 2}}}
        obj = CObj(spec)
        self.assertEqual(obj.dump(), spec)
        # modify map
        obj.cc['key3'] = AObj({'b': 3})
        self.assertEqual(
            obj.dump(),
            {'cc': {
                'key1': {
                    'b': 1
                },
                'key2': {
                    'b': 2
                },
                'key3': {
                    'b': 3
                }
            }})
        # replace child
        obj.attach_child('cc', map_(AObj)({'key3': {'b': 1}}))
        self.assertEqual(obj.dump(), {'cc': {'key3': {'b': 1}}})

        # _List
        spec = {'ccc': [{'a': 1, 'b': 2}, {'a': 2, 'b': 3}]}
        obj = CObj(spec)
        self.assertEqual(obj.dump(), spec)
        # modify list
        obj.ccc.append(AObj({'b': 4}))
        self.assertEqual(
            obj.dump(), {'ccc': [{
                'a': 1,
                'b': 2
            }, {
                'a': 2,
                'b': 3
            }, {
                'b': 4
            }]})
        # replace child
        obj.attach_child('ccc', list_(AObj)([{'b': 1}, {'b': 4}]))
        self.assertEqual(obj.dump(), {'ccc': [{'b': 1}, {'b': 4}]})

    def test_resolve(self):
        """ [Base2Obj, _Map, _List].resolve
        """
        # Base2Obj
        obj = AObj({'a': 1, 'c': {'bb': 2}})
        self.assertEqual(obj.resolve('a'), 1)
        resolved = obj.resolve('c')
        self.assertTrue(isinstance(resolved, BObj))
        self.assertEqual(resolved.resolve('bb'), 2)
        self.assertEqual(obj.resolve(['c', 'bb']), 2)

        # _Map
        obj = CObj({'cc': {'key1': {'a': 1}, 'key2': {'b': 2}}})
        self.assertEqual(obj.resolve(['cc', 'key2', 'b']), 2)
        resolved = obj.resolve('cc')
        self.assertTrue(issubclass(resolved.__class__, _Map))
        self.assertEqual(resolved.resolve(['key1', 'a']), 1)

        # _List
        obj = CObj({'ccc': [{'a': 1, 'b': 2}, {'a': 2, 'b': 3}]})
        self.assertEqual(obj.resolve(['ccc', '1', 'a']), 2)
        resolved = obj.resolve('ccc')
        self.assertTrue(issubclass(resolved.__class__, _List))
        self.assertEqual(resolved.resolve(['0', 'b']), 2)

        # _Map of _List
        obj = DObj({
            'd1': {
                'key1': [{
                    'b': 1
                }, {
                    'b': 2
                }],
                'key2': [{
                    'b': 3
                }, {
                    'b': 4
                }]
            }
        })
        self.assertEqual(obj.resolve(['d1', 'key2', '1', 'b']), 4)

        # _List of _Map
        obj = DObj({
            'd2': [{
                'key1': {
                    'b': 1
                },
                'key2': {
                    'b': 2
                }
            }, {
                'key3': {
                    'b': 3
                },
                'key4': {
                    'b': 4
                }
            }]
        })
        self.assertEqual(obj.resolve(['d2', '1', 'key4', 'b']), 4)

        # _Map of _Map
        obj = DObj({
            'd3': {
                'key1': {
                    'key11': {
                        'b': 1
                    },
                    'key12': {
                        'b': 2
                    }
                },
                'key2': {
                    'key21': {
                        'b': 3
                    },
                    'key22': {
                        'b': 4
                    }
                }
            }
        })
        self.assertEqual(obj.resolve(['d3', 'key2', 'key21', 'b']), 3)

        # dict
        obj = AObj({'b': {'a': 1, 'b': 2}})
        self.assertEqual(obj.resolve(['b', 'a']), 1)

        # list
        obj = AObj({'b': [1, 2, 3]})
        self.assertEqual(obj.resolve(['b', '0']), 1)

    def test_merge_children(self):
        """ Base2Obj.merge_children
        """
        obj_1 = GObj({'a': {'bb': 'a'}})
        self.assertEqual(list(obj_1.get_children().keys()), ['a'])
        obj_2 = GObj({'b': {'bb': 'b'}})
        obj_1.merge_children(obj_2)
        self.assertEqual(
            sorted(list(obj_1.get_children().keys())), sorted(['a', 'b']))
        self.assertEqual(list(obj_2.get_children().keys()), ['b'])

    def test_key_and_name_different(self):
        """ property name of key to underlying dict can be different
        """
        obj = HObj({'a': 1, 'b': 2})
        self.assertEqual(obj.a, 2)  # should be the value of 'b'

    def test_inherit_overwrite_fields(self):
        """ when inheriting, child's field would overwrite parent's
        """
        obj = IObj({'a': 1, 'cc': 100})
        self.assertEqual(obj.a, 100)

    def test_field_restricted(self):
        """ when restricted, should not existed in key
        """
        obj = JObj({'a': 1, 'b': 1})
        self.assertRaises(Exception, getattr, obj, 'a')
        self.assertRaises(Exception, getattr, obj, 'b')
        obj = JObj({})
        # could access 'b' because of default
        self.assertEqual(obj.b, 'hi')

    def test_recursive_field(self):
        """ field reference to self
        """
        obj = KObj({'k1': {'k1': {'k1': {'a': 2}}}, 'a': 1})
        self.assertTrue(isinstance(obj, KObj))
        self.assertEqual(obj.a, 1)
        self.assertTrue(isinstance(obj.k1, KObj))
        self.assertTrue(isinstance(obj.k1.k1, KObj))
        self.assertEqual(obj.k1.k1.k1.a, 2)

    def test_path(self):
        """ validate _path_ property
        """
        # child field, missing, or different
        obj = AObj({'c': {'bb': 1}})
        self.assertEqual(obj.get_path(), None)
        self.assertEqual(obj.c.get_path(), 'c')

        # _Map
        obj = CObj({'cc': {'key1': {'a': 1}, 'key2': {'b': 2}}})
        self.assertEqual(obj.cc['key1'].get_path(), 'cc/key1')

        # _List
        obj = CObj({'ccc': [{'a': 1, 'b': 2}, {'a': 2, 'b': 3}]})
        self.assertEqual(obj.ccc[0].get_path(), 'ccc/0')

        # _Map of _List
        obj = DObj({
            'd1': {
                'key1': [{
                    'b': 1
                }, {
                    'b': 2
                }],
                'key2': [{
                    'b': 3
                }, {
                    'b': 4
                }]
            }
        })
        self.assertEqual(obj.d1['key1'][0].get_path(), 'd1/key1/0')

        # _List of _Map
        obj = DObj({
            'd2': [{
                'key1': {
                    'b': 1
                },
                'key2': {
                    'b': 2
                }
            }, {
                'key3': {
                    'b': 3
                },
                'key4': {
                    'b': 4
                }
            }]
        })
        self.assertEqual(obj.d2[0]['key1'].get_path(), 'd2/0/key1')

        # _Map of _Map
        obj = DObj({
            'd3': {
                'key1': {
                    'key11': {
                        'b': 1
                    },
                    'key12': {
                        'b': 2
                    }
                },
                'key2': {
                    'key21': {
                        'b': 3
                    },
                    'key22': {
                        'b': 4
                    }
                }
            }
        })
        self.assertEqual(obj.d3['key1']['key11'].get_path(), 'd3/key1/key11')

    def test_renamed(self):
        """ make sure renamed works
        """
        obj = AObj({'a': 101})
        self.assertEqual(obj.a, 101)
        self.assertEqual(obj.d3_renamed, 101)

        # should inherit __renamed__
        obj = FObj({'a': 102})
        self.assertEqual(obj.a, 102)
        self.assertEqual(obj.d3_renamed, 102)

    def test_parent(self):
        obj = CObj({
            'cc': {
                'key1': {
                    'a': 1
                },
                'key2': {
                    'b': 2
                }
            },
            'ccc': [{
                'a': 1
            }, {
                'a': 2
            }]
        })
        self.assertEqual(id(obj.cc.get_parent()), id(obj))
        self.assertEqual(id(obj.ccc.get_parent()), id(obj))

        map_c = obj.cc
        self.assertEqual(id(map_c['key1'].get_parent()), id(map_c))
        self.assertEqual(id(map_c['key2'].get_parent()), id(map_c))

        list_c = obj.ccc
        self.assertEqual(id(list_c[0].get_parent()), id(list_c))
        self.assertEqual(id(list_c[1].get_parent()), id(list_c))

        obj_a = obj.cc['key1']
        obj_b = BObj({'bb': 1})
        obj_a.attach_child('c', obj_b)
        self.assertEqual(id(obj_b.get_parent()), id(obj_a))

    def test_override_children(self):
        spec = {
            'cc': {
                'key1': {
                    'a': 1,
                    'b': 3
                },
                'key2': {
                    'b': 2
                },
                'key3': {
                    'b': 3
                },
                'key4': {
                    'c': {
                        'bb': 5
                    }
                }
            },
            'ccc': [{
                'a': 1
            }, {
                'a': 2
            }]
        }
        obj_a1 = AObj(spec['cc']['key1'])
        obj_a2 = AObj(spec['cc']['key2'])
        obj_a3 = AObj(spec['ccc'][0])
        obj_a4 = AObj(spec['ccc'][1])
        obj_b = BObj(spec['cc']['key4']['c'])

        obj = CObj(
            spec,
            override={
                'cc/key1': obj_a1,
                'cc/key2': obj_a2,
                'cc/key4/c': obj_b,
                'ccc/0': obj_a3,
                'ccc/1': obj_a4
            })

        # make sure we didn't create new children
        self.assertEqual(id(obj.cc['key1']), id(obj_a1))
        self.assertEqual(id(obj.cc['key2']), id(obj_a2))
        self.assertEqual(id(obj.cc['key4'].c), id(obj_b))
        self.assertEqual(id(obj.ccc[0]), id(obj_a3))
        self.assertEqual(id(obj.ccc[1]), id(obj_a4))

    def test_readonly(self):
        obj = AObj({'d': 101})

        # allow to overwrite
        obj.d = 102
        self.assertEqual(obj.d, 102)

        # allow to overwrite via 'rename'
        obj.d4_renamed = 103
        self.assertEqual(obj.d4_renamed, 103)
        self.assertEqual(obj.d, 103)

        # deny to overwrite via 'rename' when not readonly
        def _test():
            obj.d3_renamed = 105

        self.assertRaises(Exception, _test)

    def test_eq(self):
        obj = KObj({'b': ['a', 'b'], 'c': {'a': 'ca', 'b': 'cb'}})

        self.assertEqual(obj.b, ['a', 'b'])
        self.assertEqual(obj.c, {'a': 'ca', 'b': 'cb'})
        self.assertNotEqual(obj.b, ['a', 'b', 'c'])
        self.assertNotEqual(obj.c, {'a': 'ca', 'b': 'cb', 'c': 'cc'})

    def test_map_get(self):
        obj = KObj({'c': {'a': 'ca', 'b': 'cb'}})
        self.assertEqual(obj.c.get('a'), 'ca')
        self.assertEqual(obj.c.get('c'), None)
        self.assertEqual(obj.c.get('c', default='default'), 'default')

    def test_map_len(self):
        obj = KObj({'c': {'a': 'ca', 'b': 'cb'}})
        self.assertEqual(len(obj.c), 2)

    def test_get_attrs(self):
        """ make sure Base2Obj's get_attrs works
        """
        obj = BObj({})

        self.assertEqual(None, obj.get_attrs('test'))

        attr_1 = obj.get_attrs('test', BGroup)
        self.assertTrue(isinstance(attr_1, BGroup))

        attr_2 = obj.get_attrs('test', BGroup)
        self.assertEqual(id(attr_1), id(attr_2))

        self.assertNotEqual(None, obj.get_attrs('test'))

    def test_dump_empty(self):
        obj = AObj({'a': 0, 'b': ''})

        self.assertTrue('a' in obj.dump())
        self.assertTrue('b' in obj.dump())
        self.assertFalse('c' in obj.dump())
