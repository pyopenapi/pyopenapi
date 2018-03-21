# -*- coding: utf-8 -*-

from __future__ import absolute_import
import types
import copy
import itertools

import six

from ...utils import jp_compose, jp_split
from ...errs import FieldNotExist


def field(key, required=False, default=None, restricted=False, readonly=True):
    """ property factory for primitives(string, int, ...)
    Args:
     - key: the key to access this field in json
     - required: if this field is required, would raise exception if corresponding field doesn't
                 existed in json
     - default: default value to return when corresponding field doesn't existed in json
     - restricted: this value should not exist in json
    """

    def _getter_(self):
        if key in self.spec:
            if restricted:
                raise Exception(
                    'this field is restricted, must not be specified: {}:{}'.
                    format(str(type(self)), key))
            return self.spec[key]
        if required:
            raise Exception('property not found: {} in {}'.format(
                key, self.__class__.__name__))
        return default

    def _writer_(self, val):
        self.spec[key] = val

    return property(_getter_, None if readonly else _writer_)


def internal(key, default=None):
    """ property factory for internal usage fields
    """

    def _getter_(self):
        if key in self.internal:
            return self.internal[key]
        return default

    def _setter_(self, val):
        self.internal[key] = val

    return property(_getter_, _setter_)


def rename(key):
    """ property factory for 'renamed' property.
    For some camel-cased property, we would make them snake-stype
    for fulfill python's usage.

    For child that might be targeted by '$ref', we can't rename it
    directly because the resolving would be failed.

    This property factory provide a redirection to actual property
    and should only declared under __internal__
    """

    def _getter_(self):
        return getattr(self, key)

    def _setter_(self, val):
        return setattr(self, key, val)

    return property(_getter_, _setter_)


def child(key, child_builder=None, required=False, default=None):
    """ property factory for nested BaseObj
    Args:
     - key: the key to access this field in json
     - cls: the class to handle nested object, the __init__ of it should be this form: (self, val),
            where 'val' is something parsed from json. or a function accept 'val'
     - required: if this field is required, would raise exception if corresponding field doesn't
                 existed in json
    """

    def _getter_(self):
        if key in self.children:
            return self.children[key]

        # check if we have any overriden children
        ovr = self.override.get(key, {})
        chd = ovr.get('', None)
        if chd:
            self.children[key] = chd
            return chd

        # lazy initialize of children
        val = None
        if key in self.spec:
            val = self.spec[key]
        else:
            if required:
                raise FieldNotExist('child not found: {} in {}, {}'.format(
                    key, self.__class__.__name__, self.get_path()))

        if val is None and default is not None:
            val = copy.copy(default)

        if val is not None:
            chd = child_builder(
                val, path=jp_compose(key, base=self.get_path()), override=ovr)
            self.children[key] = chd
            return chd
        return None

    def _setter_(self, val):
        if issubclass(val.__class__, (Base2Obj, _Map, _List)):
            self.children[key] = val
        else:
            raise Exception(
                'assignment of this type of object is prohibited: {}, {}'.
                format(str(type(val)), self.get_path()))

    return property(_getter_, _setter_)


class _Base(object):
    def __init__(self, spec, path=None, override=None):
        self.__path = path
        self.__parent = None
        self.spec = spec
        self.override = {}
        # inside 'override':
        #   (first token of jp_split) => (reminder of jp_split, value)

        self.children_cache = {}

        # setup override
        for k, val in six.iteritems(override or {}):
            tokens = jp_split(k, 1)
            if tokens:
                self.override.setdefault(tokens[0], {}).update({
                    tokens[1] if len(tokens) > 1 else '':
                    val
                })
            else:
                raise Exception(
                    'invalid token found for "override": {}, in {}'.format(
                        k, path))

    def is_set(self, k):
        """ check if a key is setted from Swagger API document
        :param k: the key to check
        :return: True if the key is setted. False otherwise, it means we would get value
        from default from Field.
        """
        return k in self.spec

    def get_children_cache(self):
        return self.children_cache

    def invalidate_children_cache(self):
        self.children_cache = {}

    def update_children_cache(self, cache):
        self.children_cache = cache

    def get_parent(self):
        """ get parent object
        :return: the parent object.
        :rtype: a subclass of BaseObj.
        """
        return self.__parent

    def set_parent(self, parent):
        self.__parent = parent

    def get_path(self):
        return self.__path


def list_(builder):
    """ class factory for _Map, would create a new class based on _List
    and assign __child_class__
    Args:
     - builder: child class, whose __init__ in the form: (self, val), where 'val' is something parsed from json,
              would be assigned to __child_builder__ of the newly created class, or a function accept a argument in dict.
    """
    return type('List_' + builder.__name__, (_List, ),
                dict(
                    __child_builder__=builder,
                    __child_builder_unbound__=isinstance(
                        builder, types.FunctionType),
                ))


class _List(_Base):
    """ container type: list of json. 'val' should be an list composed of
    object with the same property-set. The constructor would call its __child_class__
    on all those objects.
    """

    __child_builder_unbound__ = False

    def __init__(self, spec, path=None, override=None):
        super(_List, self).__init__(spec, path, override)
        self.__elm = []

        if not isinstance(spec, list):
            raise Exception(
                'should be a list when constructing _List, not {}, {}'.format(
                    str(type(spec)), path))

        # generate children for all keys in spec
        for idx, e in enumerate(spec):
            idx = str(idx)

            ovr = self.override.get(idx, {})
            elm = ovr.get('', None)
            if not elm:
                path = jp_compose(idx, base=self.get_path())
                if self.__child_builder_unbound__:
                    elm = self.__child_builder__.__func__(  # pylint: disable=no-member
                        e,
                        path=path,
                        override=ovr)
                else:
                    elm = self.__child_builder__(e, path=path, override=ovr)  # pylint: disable=no-member

            if hasattr(elm, 'set_parent'):
                elm.set_parent(self)

            self.__elm.append(elm)

    def resolve(self, parts):
        if isinstance(parts, six.string_types):
            parts = [parts]

        obj = self
        if parts:
            idx = parts.pop(0)
            return self.__elm[int(idx)].resolve(parts)
        return obj

    def merge_children(self, other):
        raise NotImplementedError()

    def compare(self, other, base=None):
        # pylint: disable=unidiomatic-typecheck
        if type(self) != type(other):
            return False, ''

        if len(self) != len(other):
            return False, ''

        for idx, (self_, other_) in enumerate(zip(self, other)):
            new_base = jp_compose(str(idx), base=base)
            if isinstance(self_, six.string_types + six.integer_types):
                return self_ == other_, new_base

            same, name = self_.compare(other_, base=new_base)
            if not same:
                return same, name

        return True, ''

    def dump(self):
        ret = []
        if not self.__elm:
            return ret

        is_primitive = not hasattr(self.__elm[0], 'dump')
        if is_primitive:
            return copy.copy(self.__elm)

        for e in self.__elm:
            ret.append(e.dump())
        return ret

    # pylint: disable=no-self-use
    def get_field_names(self):
        return []

    def get_children(self):
        ret = self.get_children_cache()
        if ret:
            return ret

        for idx, obj in enumerate(self.__elm):
            if isinstance(obj, Base2Obj):
                ret[str(idx)] = obj
            elif isinstance(obj, (
                    _Map,
                    _List,
            )):
                children = obj.get_children()
                for name in children:
                    ret[jp_compose([str(idx), name])] = children[name]

        self.update_children_cache(ret)
        return ret

    def __iter__(self):
        for e in self.__elm:
            yield e

    def __getitem__(self, idx):
        return self.__elm[idx]

    def __len__(self):
        return len(self.__elm)

    def __eq__(self, other):
        return self.__elm == other

    def append(self, obj):
        self.invalidate_children_cache()

        return self.__elm.append(obj)

    def extend(self, other):
        self.invalidate_children_cache()

        return self.__elm.extend(other)


def map_(builder):
    """ class factory for _Map, would create a new class based on _Map
    and assign __child_class__
    Args:
     - builder: child class, whose __init__ in the form: (self, val), where 'val' is something parsed from json,
              would be assigned to __child_builder__ of the newly created class, or a function accept a argument in dict.
    """

    return type('Map_' + builder.__name__, (_Map, ),
                dict(
                    __child_builder__=builder,
                    __child_builder_unbound__=isinstance(
                        builder, types.FunctionType),
                ))


class _Map(_Base):
    """ container type: map of json. 'val' should be an dict composed of
    objects with the same property-set. The constructor would call its __child_class__
    on all those objects.
    """

    __child_builder_unbound__ = False

    def __init__(self, spec, path=None, override=None):
        super(_Map, self).__init__(spec, path, override)
        self.__elm = {}

        if not isinstance(spec, dict):
            raise Exception(
                'should be an instance of dict when reaching _Map constructor, not {}, {}'.
                format(str(type(spec)), self.get_path()))

        # generate children for all keys in spec
        for k in spec:
            ovr = self.override.get(k, {})
            elm = ovr.get('', None)
            if not elm:
                path = jp_compose(str(k), base=self.get_path())
                if self.__child_builder_unbound__:
                    elm = self.__child_builder__.__func__(  # pylint: disable=no-member
                        spec[k],
                        path=path,
                        override=ovr)
                else:
                    elm = self.__child_builder__(  # pylint: disable=no-member
                        spec[k],
                        path=path,
                        override=ovr)

            if hasattr(elm, 'set_parent'):
                elm.set_parent(self)

            self.__elm[k] = elm

    def resolve(self, parts):
        if isinstance(parts, six.string_types):
            parts = [parts]

        obj = self
        if parts:
            key = parts.pop(0)
            return self.__elm[key].resolve(parts)
        return obj

    def merge_children(self, other):
        raise NotImplementedError()

    def compare(self, other, base=None):
        # pylint: disable=unidiomatic-typecheck
        if type(self) != type(other):
            return False, ''

        diff = list(set(self.keys()) - set(other.keys()))
        if diff:
            return False, jp_compose(diff[0], base=base)
        diff = list(set(other.keys()) - set(self.keys()))
        if diff:
            return False, jp_compose(diff[0], base=base)

        for name in self.__elm:
            new_base = jp_compose(name, base=base)
            if isinstance(self.__elm[name],
                          six.string_types + six.integer_types):
                return self.__elm[name] == other[name], new_base

            same, name = self.__elm[name].compare(other[name], base=new_base)
            if not same:
                return same, name

        return True, ''

    def dump(self):
        ret = {}
        for k, obj in six.iteritems(self.__elm):
            if hasattr(obj, 'dump') and callable(obj.dump):
                ret[k] = obj.dump()
            else:
                ret[k] = obj

        return ret

    # pylint: disable=no-self-use
    def get_field_names(self):
        return []

    def keys(self):
        return self.__elm.keys()

    def get_children(self):
        ret = self.get_children_cache()
        if ret:
            return ret

        for name, obj in six.iteritems(self.__elm):
            if isinstance(obj, Base2Obj):
                ret[name] = obj
            elif isinstance(obj, (
                    _Map,
                    _List,
            )):
                children = obj.get_children()
                for key in children:
                    ret[jp_compose([name, key])] = children[key]

        self.update_children_cache(ret)
        return ret

    def __getitem__(self, key):
        return self.__elm[key]

    def __setitem__(self, key, obj):
        self.invalidate_children_cache()

        self.__elm[key] = obj

    def __contains__(self, elm):
        return elm in self.__elm

    def __eq__(self, other):
        return self.__elm == other

    def iteritems(self):
        return six.iteritems(self.__elm)

    def itervalues(self):
        return six.itervalues(self.__elm)

    def items(self):
        return six.viewitems(self.__elm)

    def iterkeys(self):
        return six.iterkeys(self.__elm)

    def get(self, key, default=None):
        return self.__elm.get(key, default)

    def __len__(self):
        return len(self.__elm)


class FieldMeta(type):
    """ metaclass to init fields, similar to the one in base.py
    """

    def __new__(mcs, name, bases, spc):
        """ scan through MRO to get a merged list of fields and create them
        """
        fields = spc.setdefault('__fields__', {})
        children = spc.setdefault('__children__', {})
        intl = spc.setdefault('__internal__', {})

        def _from_parent_(base, spec, name):
            parent_spec = getattr(base, name, None)
            if parent_spec:
                tmp = {}
                for k in set(parent_spec.keys()) - set(spec.keys()):
                    tmp[k] = parent_spec[k]
                spec.update(tmp)

        for base in bases:
            _from_parent_(base, fields, '__fields__')
            _from_parent_(base, children, '__children__')
            _from_parent_(base, intl, '__internal__')

        def _update_to_spc(default_builder, spec):
            for name, args in six.iteritems(spec):
                args = copy.copy(args)
                builder = args.pop('builder', None) or default_builder
                spc[name] = builder(args.pop('key', None) or name, **args)

        _update_to_spc(field, fields)
        _update_to_spc(internal, intl)
        _update_to_spc(child, children)

        return type.__new__(mcs, name, bases, spc)


class Base2Obj(_Base):
    """ Base implementation of all Open API objects
    """

    __children__ = {}
    __fields__ = {}
    __internal__ = {}

    def __init__(self, spec, path=None, override=None):
        """ constructor
        Args:
            - spec: the open api spec in dict
            - path:
            - override:
        """
        super(Base2Obj, self).__init__(spec, path, override)
        self.children = {}
        self.internal = {}
        self.attrs = {}

        # traverse through children
        for name in self.__children__:
            # trigger the getter of children, it will create it if exist
            chd = getattr(self, name)
            if chd and hasattr(chd, 'set_parent'):
                chd.set_parent(self)

    def resolve(self, parts):
        """ resolve a list of tokens to an child object
        :param list ts: list of tokens
        """
        if isinstance(parts, six.string_types):
            parts = [parts]

        obj = self
        while parts:
            name = parts.pop(0)

            if issubclass(obj.__class__, Base2Obj):
                obj = getattr(obj, name)
            elif isinstance(obj, list):
                obj = obj[int(name)]
            elif isinstance(obj, dict):
                obj = obj[name]

            if issubclass(obj.__class__, (Base2Obj, _Map, _List)) and parts:
                return obj.resolve(parts)
        return obj

    def merge_children(self, other):
        """ merge 1st layer of children from other object,
        :param BaseObj other: the source object to be merged from.
        """
        for name in self.__children__:
            if not getattr(self, name):
                obj = getattr(other, name)
                if obj:
                    setattr(self, name, obj)

        self.invalidate_children_cache()

    def compare(self, other, base=None):
        """ comparison, will return the first difference, mainly used for testing """

        # pylint: disable=unidiomatic-typecheck
        if type(self) != type(other):
            return False, ''

        def _cmp_(name, self_, other_):
            if isinstance(self_, six.string_types + six.integer_types):
                return self_ == other_, name

            # pylint: disable=unidiomatic-typecheck
            if type(self_) != type(other_):
                return False, name
            if isinstance(self_, (Base2Obj, _Map, _List)):
                return self_.compare(other_, base=name)
            if isinstance(self_, list):
                for i, elm in zip(range(len(self_)), self_):
                    same, location = _cmp_(
                        jp_compose(str(i), name), elm, other_[i])
                    if not same:
                        return same, location
            elif isinstance(self_, dict):
                # dict diff is complex, so we just
                # compare if any key diff here
                diff = list(set(self_.keys()) - set(other_.keys()))
                if diff:
                    return False, jp_compose(str(diff[0]), name)
                diff = list(set(other_.keys()) - set(self_.keys()))
                if diff:
                    return False, jp_compose(str(diff[0]), name)
                for k, val in six.iteritems(self_):
                    same, location = _cmp_(jp_compose(k, name), val, other_[k])
                    if not same:
                        return same, location
            else:
                # unknown type, delegate to default compare
                return self_ == other_, name
            return True, ''

        for name in itertools.chain(
                six.iterkeys(self.__fields__), six.iterkeys(self.__children__)):
            same, location = _cmp_(
                jp_compose(name, base), getattr(self, name), getattr(
                    other, name))
            if not same:
                return same, location

        return True, ''

    def dump(self):
        """ dump Swagger Spec in dict(which can be
        convert to JSON)
        """
        ret = {}

        children = set([name for name in self.__children__])
        fields = set([name for name in self.__fields__])

        # dump children first
        for name in children:
            child_ = getattr(self, name)
            if child_:
                ret[name] = child_.dump()
                fields.discard(name)

        # dump each field
        for name in fields:
            if not self.is_set(name):
                continue

            obj = getattr(self, name)
            if obj is None:
                continue

            ret[name] = obj

        return ret

    def attach_child(self, name, obj):
        if name not in self.__children__:
            raise Exception(
                'attemp to attach a children not in child fields {}:{}, {}'.
                format(str(type(self)), name, self.get_path()))

        setattr(self, name, obj)
        if hasattr(obj, 'set_parent'):
            obj.set_parent(self)

        self.invalidate_children_cache()

    @classmethod
    def attach_field(cls, name, **field_descriptor):
        desc = copy.copy(field_descriptor)

        builder = desc.pop('builder')
        key = desc.pop('key', None)
        setattr(cls, name, builder(key or name, **desc))
        if builder.__name__ == 'child':
            cls.__children__[name] = field_descriptor
        elif builder.__name__ == 'internal':
            cls.__internal__[name] = field_descriptor

    def get_field_names(self):
        """ get list of field names defined in Swagger spec
        :return: a list of field names
        :rtype: a list of str
        """
        return [name for name in set(self.__fields__) | set(self.__children__)]

    def get_children(self):
        """ get children objects
        :rtype: a dict of children {child_name: child_object}
        """
        ret = self.get_children_cache()
        if ret:
            return ret

        for name in self.__children__:
            obj = getattr(self, name)
            if not obj:
                continue
            if isinstance(obj, Base2Obj):
                ret[name] = obj
            elif isinstance(obj, (
                    _Map,
                    _List,
            )):
                children = obj.get_children()
                for child_name in children:
                    ret[jp_compose([name, child_name])] = children[child_name]

        self.update_children_cache(ret)
        return ret

    def get_attrs(self, namespace, group_cls=None):
        """ attach an pyopenapi.migration.spec.AttributeGroup

        Args:
         - namespace: different attribute goups are separated/accessed by namespace
         - group_cls: the AttributeGroup to init when None is found
        """

        if namespace in self.attrs:
            return self.attrs[namespace]

        if group_cls is None:
            return None

        group = group_cls({})
        self.attrs[namespace] = group
        return group


Base2 = six.with_metaclass(FieldMeta, Base2Obj)
