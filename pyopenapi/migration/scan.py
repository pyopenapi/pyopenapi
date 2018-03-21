# -*- coding: utf-8 -*-

from __future__ import absolute_import
import six

from .spec import Base2Obj


def default_tree_traversal(root, leaves):
    """ default tree traversal """
    objs = [('#', root)]
    while objs:
        path, obj = objs.pop()

        # name of child are json-pointer encoded, we don't have
        # to encode it again.
        if obj.__class__ not in leaves:
            objs.extend(
                map(lambda i: ('/'.join([path, i[0]]), i[1]),
                    six.iteritems(obj.get_children())))

        # the path we expose here follows JsonPointer described here
        #   http://tools.ietf.org/html/draft-ietf-appsawg-json-pointer-07
        yield path, obj


class DispatcherMeta(type):
    """ metaclass for Dispatcher
    """

    def __new__(mcs, name, bases, spc):
        if 'obj_route' not in spc.keys():
            # forcely create a new obj_route
            # but not share the same one with parents.
            spc['obj_route'] = {}
            spc['result_fn'] = [None]

        return type.__new__(mcs, name, bases, spc)


class Dispatcher(six.with_metaclass(DispatcherMeta, object)):
    """ Dispatcher
    """
    obj_route = {}
    result_fn = [None]

    @classmethod
    def __add_route(cls, target_cls, func):
        """
        """
        if not issubclass(target_cls, Base2Obj):
            raise ValueError(
                'target_cls should be a subclass of Base2Obj, but got:' +
                str(target_cls))

        # allow register multiple handler function
        # against one object
        cls.obj_route.setdefault(target_cls, []).append(func)

    @classmethod
    def register(cls, target_classes):
        """
        """

        def outer_func(func):
            # what we did is simple,
            # register target_cls as key, and f as callback
            # then keep this record in cls.
            for x in target_classes:
                cls.__add_route(x, func)

            # nothing is decorated. Just return original one.
            return func

        return outer_func

    @classmethod
    def result(cls, func):
        """
        """

        # avoid bound error
        cls.result_fn = [func]
        return func


def _build_route(routes):
    ret = []
    for route in routes:
        for obj in six.itervalues(vars(route.__class__)):
            if not isinstance(obj, DispatcherMeta):
                continue

            ret.append((route, obj.obj_route, obj.result_fn[0]))
            break

    return ret


def _handle_cls(cls, app, path, obj, the_self, route, res):
    funcs = route.get(cls, None)
    if funcs:
        for handler in funcs:
            ret = handler(the_self, path, obj, app)
            if res:
                res(the_self, ret)


def _handle_cls_without_app(cls, path, obj, the_self, route, res):
    funcs = route.get(cls, None)
    if not funcs:
        return
    for handler in funcs:
        ret = handler(the_self, path, obj)
        if res:
            res(the_self, ret)


class Scanner(object):
    """ Scanner
    """

    def __init__(self, app):
        super(Scanner, self).__init__()
        self.__app = app

    @property
    def app(self):
        return self.__app

    def scan(self, route, root, nexter=default_tree_traversal, leaves=None):
        leaves = leaves or []

        if root is None:
            raise ValueError('Can\'t scan because root==None')

        merged_r = _build_route(route)
        for path, obj in nexter(root, leaves):
            for args in merged_r:
                for cls in obj.__class__.__mro__[:-1]:
                    if cls is Base2Obj:
                        break
                    _handle_cls(cls, self.app, path, obj, *args)


def scan(route, root, nexter=default_tree_traversal, leaves=None):
    """ Scanner v2, the main change is to remove 'app' from default input. The depnedencies
    between Scannner and App should be decoupled.
    """
    leaves = leaves or []

    if root is None:
        raise ValueError('Can\'t scan because root==None')

    merged_r = _build_route(route)
    for path, obj in nexter(root, leaves):
        for args in merged_r:
            _handle_cls_without_app(obj.__class__, path, obj, *args)
