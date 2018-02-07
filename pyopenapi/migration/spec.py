from ..utils import jp_compose, jp_split
from ..errs import FieldNotExist
import six
import types
import copy
import os


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
                raise Exception('this field is restricted, must not be specified: {}:{}'.format(str(type(self)), key))
            return self.spec[key]
        if required:
            raise Exception('property not found: {} in {}'.format(key, self.__class__.__name__))
        return default

    def _writer_(self, v):
        self.spec[key] = v

    return property(_getter_, None if readonly else _writer_)


def internal(key, default=None):
    """ property factory for internal usage fields
    """
    def _getter_(self):
        if key in self.internal:
            return self.internal[key]
        return default

    def _setter_(self, v):
        self.internal[key] = v

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

    def _setter_(self, v):
        return setattr(self, key, v)

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
                raise FieldNotExist('child not found: {} in {}, {}'.format(key, self.__class__.__name__, self.path))

        if val is None and default is not None:
            val = copy.copy(default)

        if val is not None:
            chd = child_builder(val, path=jp_compose(key, base=self.path), override=ovr)
            self.children[key] = chd
            return chd
        else:
            return None

    def _setter_(self, v):
        if issubclass(v.__class__, (Base2Obj, _Map, _List)):
            self.children[key] = v
        else:
            raise Exception('assignment of this type of object is prohibited: {}, {}'.format(str(type(v)), self.path))

    return property(_getter_, _setter_)


class _Base(object):
    def __init__(self, spec, path=None, override=None):
        self._path = path
        self._parent = None
        self.spec = spec
        self.override = {}
        # inside 'override':
        #   (first token of jp_split) => (reminder of jp_split, value)

        # setup override
        for k, v in six.iteritems(override or {}):
            tokens = jp_split(k, 1)
            if len(tokens) > 0:
                self.override.setdefault(tokens[0], {}).update({
                    tokens[1] if len(tokens) > 1 else '': v
                })
            else:
                raise Exception('invalid token found for "override": {}, in {}'.format(k, path))

    def is_set(self, k):
        """ check if a key is setted from Swagger API document
        :param k: the key to check
        :return: True if the key is setted. False otherwise, it means we would get value
        from default from Field.
        """
        return k in self.spec

    @property
    def parent(self):
        """ get parent object
        :return: the parent object.
        :rtype: a subclass of BaseObj.
        """
        return self._parent

    @parent.setter
    def parent(self, v):
        self._parent = v

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, v):
        self._path = v


def list_(builder):
    """ class factory for _Map, would create a new class based on _List
    and assign __child_class__
    Args:
     - builder: child class, whose __init__ in the form: (self, val), where 'val' is something parsed from json,
              would be assigned to __child_builder__ of the newly created class, or a function accept a argument in dict.
    """
    return type(
        'List_' + builder.__name__,
        (_List,),
        dict(
            __child_builder__=builder,
            __child_builder_unbound__ = isinstance(builder, types.FunctionType),
        )
    )


class _List(_Base):
    """ container type: list of json. 'val' should be an list composed of
    object with the same property-set. The constructor would call its __child_class__
    on all those objects.
    """
    def __init__(self, spec, path=None, override=None):
        super(_List, self).__init__(spec, path, override)
        self.__elm = []

        if not isinstance(spec, list):
            raise Exception('should be a list when constructing _List, not {}, {}'.format(str(type(spec)), path))

        # generate children for all keys in spec
        for idx, e in enumerate(spec):
            idx = str(idx)

            ovr = self.override.get(idx, {})
            elm = ovr.get('', None)
            if not elm:
                path = jp_compose(idx, base=self.path)
                if self.__child_builder_unbound__:
                    elm = self.__child_builder__.__func__(e, path=path, override=ovr)
                else:
                    elm = self.__child_builder__(e, path=path, override=ovr)

            if hasattr(elm, 'parent'):
                elm.parent = self

            self.__elm.append(elm)

    def resolve(self, ts):
        if isinstance(ts, six.string_types):
            ts = [ts]

        obj = self
        if len(ts) > 0:
            t = ts.pop(0)
            return self.__elm[int(t)].resolve(ts)
        return obj

    def merge_children(self, other):
        raise NotImplementedError()

    def compare(self, other, base=None):
        if type(self) != type(other):
            return False, ''

        if len(self.__elm) != len(other.__elm):
            return False, ''

        for idx, (s, o) in enumerate(zip(self, other)):
            new_base = jp_compose(str(idx), base=base)
            if isinstance(s, six.string_types + six.integer_types):
                return s == o, new_base

            same, name = s.compare(o, base=new_base)
            if not same:
                return same, name

        return True, ''

    def dump(self):
        ret = []
        if len(self.__elm) == 0:
            return ret

        is_primitive = not hasattr(self.__elm[0], 'dump')
        if is_primitive:
            return copy.copy(self.__elm)

        for e in self.__elm:
            ret.append(e.dump())
        return ret

    @property
    def _field_names_(self):
        return []

    @property
    def _children_(self):
        ret = {}
        for idx, obj in enumerate(self.__elm):
            if isinstance(obj, Base2Obj):
                ret[str(idx)] = obj
            elif isinstance(obj, (_Map, _List,)):
                c = obj._children_
                for cc in c:
                    ret[jp_compose([str(idx), cc])] = c[cc]

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
        return self.__elm.append(obj)

    def extend(self, other):
        return self.__elm.extend(other)


def map_(builder):
    """ class factory for _Map, would create a new class based on _Map
    and assign __child_class__
    Args:
     - builder: child class, whose __init__ in the form: (self, val), where 'val' is something parsed from json,
              would be assigned to __child_builder__ of the newly created class, or a function accept a argument in dict.
    """

    return type(
        'Map_' + builder.__name__,
        (_Map,),
        dict(
            __child_builder__=builder,
            __child_builder_unbound__ = isinstance(builder, types.FunctionType),
        )
    )


class _Map(_Base):
    """ container type: map of json. 'val' should be an dict composed of
    objects with the same property-set. The constructor would call its __child_class__
    on all those objects.
    """
    def __init__(self, spec, path=None, override=None):
        super(_Map, self).__init__(spec, path, override)
        self.__elm = {}

        if not isinstance(spec, dict):
            raise Exception('should be an instance of dict when reaching _Map constructor, not {}, {}'.format(str(type(spec)), self.path))

        # generate children for all keys in spec
        for k in spec:
            ovr = self.override.get(k, {})
            elm = ovr.get('', None)
            if not elm:
                path = jp_compose(str(k), base=self.path)
                if self.__child_builder_unbound__:
                    elm = self.__child_builder__.__func__(spec[k], path=path, override=ovr)
                else:
                    elm = self.__child_builder__(spec[k], path=path, override=ovr)

            if hasattr(elm, 'parent'):
                elm.parent = self

            self.__elm[k] = elm

    def resolve(self, ts):
        if isinstance(ts, six.string_types):
            ts = [ts]

        obj = self
        if len(ts) > 0:
            t = ts.pop(0)
            return self.__elm[t].resolve(ts)
        return obj

    def merge_children(self, other):
        raise NotImplementedError()

    def compare(self, other, base=None):
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
            if isinstance(self.__elm[name], six.string_types + six.integer_types):
                return self.__elm[name] == other[name], new_base

            s, n = self.__elm[name].compare(other[name], base=new_base)
            if not s:
                return s, n

        return True, ''

    def dump(self):
        ret = {}
        for k, v in six.iteritems(self.__elm):
            if hasattr(v, 'dump') and callable(v.dump):
                ret[k] = v.dump()
            else:
                ret[k] = v

        return ret

    @property
    def _field_names_(self):
        return []

    def keys(self):
        return self.__elm.keys()

    @property
    def _children_(self):
        ret = {}
        for name, obj in six.iteritems(self.__elm):
            if isinstance(obj, Base2Obj):
                ret[name] = obj
            elif isinstance(obj, (_Map, _List,)):
                c = obj._children_
                for cc in c:
                    ret[jp_compose([name, cc])] = c[cc]

        return ret

    def __getitem__(self, key):
        return self.__elm[key]

    def __setitem__(self, key, obj):
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
    def __new__(metacls, name, bases, spc):
        """ scan through MRO to get a merged list of fields and create them
        """
        fields = spc.setdefault('__fields__', {})
        cn = spc.setdefault('__children__', {})
        intl = spc.setdefault('__internal__', {})

        def _from_parent_(s, name):
            p = getattr(b, name, None)
            if p:
                d = {}
                for k in set(p.keys()) - set(s.keys()):
                    d[k] = p[k]
                s.update(d)

        for b in bases:
            _from_parent_(fields, '__fields__')
            _from_parent_(cn, '__children__')
            _from_parent_(intl, '__internal__')

        def _update_to_spc(default_builder, fs):
            for n, args in six.iteritems(fs):
                args = copy.copy(args)
                builder = args.pop('builder', None) or default_builder
                spc[n] = builder(args.pop('key', None) or n, **args)

        _update_to_spc(field, fields)
        _update_to_spc(internal, intl)
        _update_to_spc(child, cn)

        return type.__new__(metacls, name, bases, spc)


class Base2Obj(_Base):
    """ Base implementation of all Open API objects
    """

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

        # traverse through children
        for name in self.__children__:
            # trigger the getter of children, it will create it if exist
            chd = getattr(self, name)
            if chd and hasattr(chd, 'parent'):
                chd.parent = self

    def resolve(self, ts):
        """ resolve a list of tokens to an child object
        :param list ts: list of tokens
        """
        if isinstance(ts, six.string_types):
            ts = [ts]

        obj = self
        while len(ts) > 0:
            t = ts.pop(0)

            if issubclass(obj.__class__, Base2Obj):
                obj = getattr(obj, t)
            elif isinstance(obj, list):
                obj = obj[int(t)]
            elif isinstance(obj, dict):
                obj = obj[t]

            if issubclass(obj.__class__, (Base2Obj, _Map, _List)) and len(ts):
                return obj.resolve(ts)
        return obj

    def merge_children(self, other):
        """ merge 1st layer of children from other object,
        :param BaseObj other: the source object to be merged from.
        """
        for name in self.__children__:
            if not getattr(self, name):
                o = getattr(other, name)
                if o:
                    setattr(self, name, o)

    def compare(self, other, base=None):
        """ comparison, will return the first difference, mainly used for testing """
        if type(self) != type(other):
            return False, ''

        def _cmp_(name, s, o):
            if isinstance(s, six.string_types + six.integer_types):
                return s == o, name
            if type(s) != type(o):
                return False, name
            if isinstance(s, (Base2Obj, _Map, _List)):
                return s.compare(o, base=name)
            if isinstance(s, list):
                for i, v in zip(range(len(s)), s):
                    same, n = _cmp_(jp_compose(str(i), name), v, o[i])
                    if not same:
                        return same, n
            elif isinstance(s, dict):
                # dict diff is complex, so we just
                # compare if any key diff here
                diff = list(set(s.keys()) - set(o.keys()))
                if diff:
                    return False, jp_compose(str(diff[0]), name)
                diff = list(set(o.keys()) - set(s.keys()))
                if diff:
                    return False, jp_compose(str(diff[0]), name)
                for k, v in six.iteritems(s):
                    same, n = _cmp_(jp_compose(k, name), v, o[k])
                    if not same:
                        return same, n
            else:
                # unknown type, delegate to default compare
                return s == o, name
            return True, ''

        for name in self.__fields__.keys() + self.__children__.keys():
            same, n = _cmp_(jp_compose(name, base), getattr(self, name), getattr(other, name))
            if not same:
                return same, n

        return True, ''

    def dump(self):
        """ dump Swagger Spec in dict(which can be
        convert to JSON)
        """
        ret = {}

        cs = set([name for name in self.__children__])
        fs = set([name for name in self.__fields__])

        # dump children first
        for name in cs:
            c = getattr(self, name)
            if c:
                ret[name] = c.dump()
                fs.discard(name)

        # dump each field
        for name in fs:
            o = getattr(self, name)
            if o:
                ret[name] = o

        return ret

    def attach_child(self, name, obj):
        if name not in self.__children__:
            raise Exception('attemp to attach a children not in child fields {}:{}, {}'.format(str(type(self)), name, self.path))

        setattr(self, name, obj)
        if hasattr(obj, 'parent'):
            obj.parent = self

    @classmethod
    def attach_field(kls, name, **field_descriptor):
        desc = copy.copy(field_descriptor)

        builder = desc.pop('builder')
        key = desc.pop('key', None)
        setattr(kls, name, builder(key or name, **desc))
        if builder.__name__ == 'child':
            kls.__children__[name] = field_descriptor
        elif builder.__name__ == 'internal':
            kls.__internal__[name] = field_descriptor

    @property
    def _field_names_(self):
        """ get list of field names defined in Swagger spec
        :return: a list of field names
        :rtype: a list of str
        """
        return [name for name in set(self.__fields__) | set(self.__children__)]

    @property
    def _children_(self):
        """ get children objects
        :rtype: a dict of children {child_name: child_object}
        """
        ret = {}
        for name in self.__children__:
            obj = getattr(self, name)
            if not obj:
                continue
            if isinstance(obj, Base2Obj):
                ret[name] = obj
            elif isinstance(obj, (_Map, _List,)):
                c = obj._children_
                for cc in c:
                    ret[jp_compose([name, cc])] = c[cc]

        return ret


Base2 = six.with_metaclass(FieldMeta, Base2Obj)

