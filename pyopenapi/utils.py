from __future__ import absolute_import
from . import consts
from .errs import CycleDetectionError
import six
import imp
import sys
import datetime
import re
import os
import operator
import functools
import pkgutil
import distutils


#TODO: accept varg
def scope_compose(scope, name, sep=consts.SCOPE_SEPARATOR):
    """ compose a new scope

    :param str scope: current scope
    :param str name: name of next level in scope
    :return the composed scope
    """

    if name == None:
        new_scope = scope
    else:
        new_scope = scope if scope else name

    if scope and name:
        new_scope = scope + sep + name

    return new_scope


def scope_split(scope, sep=consts.SCOPE_SEPARATOR):
    """ split a scope into names

    :param str scope: scope to be splitted
    :return: list of str for scope names
    """

    return scope.split(sep) if scope else [None]


class ScopeDict(dict):
    """ ScopeDict
    """

    def __init__(self, *a, **k):
        self.__sep = consts.SCOPE_SEPARATOR
        super(ScopeDict, self).__init__(*a, **k)

    @property
    def sep(self):
        """ separator property
        """
        raise TypeError('sep property is write-only')

    @sep.setter
    def sep(self, sep):
        """ update separater used here
        """
        self.__sep = sep

    def __getitem__(self, *keys):
        """ to access an obj with key: 'n!##!m...!##!z', caller can pass as key:
        - n!##!m...!##!z
        - n, m, ..., z
        - z
        when separater == !##!

        :param dict keys: keys to access via scopes.
        """
        k = six.moves.reduce(
            lambda k1, k2: scope_compose(k1, k2, sep=self.__sep),
            keys[0]) if isinstance(keys[0], tuple) else keys[0]
        try:
            return super(ScopeDict, self).__getitem__(k)
        except KeyError as e:
            ret = []
            for ik in self.keys():
                if ik.endswith(k):
                    ret.append(ik)
            if len(ret) == 1:
                return super(ScopeDict, self).__getitem__(ret[0])
            elif len(ret) > 1:
                # special case for the last token:
                #  - a!##!get
                #  - b!##!something-get
                #  and access with 'get'
                last_k = k.rsplit(self.__sep, 1)[-1]
                matched = [
                    r for r in ret if r.rsplit(self.__sep, 1)[-1] == last_k
                ]
                if len(matched) == 1:
                    return super(ScopeDict, self).__getitem__(matched[0])

                raise ValueError('Multiple occurrence of key: {0}'.format(k))

            raise e


class CycleGuard(object):
    """ Guard for cycle detection
    """

    def __init__(self):
        self.__visited = []

    def update(self, obj):
        if obj in self.__visited:
            raise CycleDetectionError('Cycle detected: {0}'.format(
                getattr(obj, '$ref', None)))
        self.__visited.append(obj)


def jp_compose(s, base=None):
    """ append/encode a string to json-pointer
    """
    if s == None:
        return base

    ss = [s] if isinstance(s, six.string_types) else s
    ss = [s.replace('~', '~0').replace('/', '~1') for s in ss]
    if base:
        ss.insert(0, base)
    return '/'.join(ss)


def jp_split(s, max_split=-1):
    """ split/decode a string from json-pointer
    """
    if s == '' or s == None:
        return []

    def _decode(s):
        s = s.replace('~1', '/')
        return s.replace('~0', '~')

    return [_decode(ss) for ss in s.split('/', max_split)]


def jr_split(s):
    """ split a json-reference into (url, json-pointer)
    """
    p = six.moves.urllib.parse.urlparse(s)
    return (normalize_url(six.moves.urllib.parse.urlunparse(p[:5] + ('', ))),
            '#' + p.fragment if p.fragment else '#')


def deref(obj, guard=None):
    """ dereference $ref
    """
    cur, guard = obj, guard or CycleGuard()
    guard.update(cur)
    while cur and getattr(cur, 'ref', None) != None:
        attrs = cur.get_attrs('migration')
        if not attrs:
            break
        if attrs.ref_obj is None:
            break

        cur = attrs.ref_obj
        guard.update(cur)

    return cur


def final(obj):
    if obj.ref:
        return obj.get_attrs('migration').final_obj or obj
    return obj


def path2url(p):
    """ Return file:// URL from a filename.
    """
    if sys.version_info.major >= 3 and sys.version_info.minor >= 4:
        import pathlib
        return pathlib.Path(p).as_uri()
    else:
        return six.moves.urllib.parse.urljoin(
            'file:', six.moves.urllib.request.pathname2url(p))


_windows_path_prefix = re.compile(r'(^[A-Za-z]:\\)')


def normalize_url(url):
    """ Normalize url
    """
    if not url:
        return url

    matched = _windows_path_prefix.match(url)
    if matched:
        return path2url(url)

    p = six.moves.urllib.parse.urlparse(url)
    if p.scheme == '':
        if p.netloc == '' and p.path != '':
            # it should be a file path
            url = path2url(os.path.abspath(url))
        else:
            raise ValueError('url should be a http-url or file path -- ' + url)

    return url


def url_dirname(url):
    """ Return the folder containing the '.json' file
    """
    p = six.moves.urllib.parse.urlparse(url)
    for e in [consts.FILE_EXT_JSON, consts.FILE_EXT_YAML]:
        if p.path.endswith(e):
            return six.moves.urllib.parse.urlunparse(
                p[:2] + (os.path.dirname(p.path), ) + p[3:])
    return url


def url_join(url, path):
    """ url version of os.path.join
    """
    p = six.moves.urllib.parse.urlparse(url)

    t = None
    if p.path and p.path[-1] == '/':
        if path and path[0] == '/':
            path = path[1:]
        t = ''.join([p.path, path])
    else:
        t = ('' if path and path[0] == '/' else '/').join([p.path, path])

    return six.moves.urllib.parse.urlunparse(
        p[:2] + (t, ) +    # os.sep is different on windows, don't use it here.
        p[3:])


def normalize_jr(jr, url=None):
    """ normalize JSON reference, also fix
    implicit reference of JSON pointer.
    input:
    - #/definitions/User
    - http://test.com/swagger.json#/definitions/User
    output:
    - http://test.com/swagger.json#/definitions/User

    input:
    - some_folder/User.json
    output:
    - http://test.com/some_folder/User.json
    """

    if jr == None:
        return jr

    idx = jr.find('#')
    path, jp = (jr[:idx], jr[idx + 1:]) if idx != -1 else (jr, None)

    if len(path) > 0:
        p = six.moves.urllib.parse.urlparse(path)
        if p.scheme == '' and url:
            p = six.moves.urllib.parse.urlparse(url)
            # it's the path of relative file
            path = six.moves.urllib.parse.urlunparse(
                p[:2] + ('/'.join([os.path.dirname(p.path), path]), ) + p[3:])
            path = derelativise_url(path)
    else:
        path = url

    if path:
        return ''.join([path, '#', jp]) if jp else path
    else:
        return '#' + jp


def _fullmatch(regex, chunk):
    m = re.match(regex, chunk)
    if m and m.span()[1] == len(chunk):
        return m
    return None


def derelativise_url(url):
    '''
    Normalizes URLs, gets rid of .. and .
    '''
    parsed = six.moves.urllib.parse.urlparse(url)
    newpath = []
    for chunk in parsed.path[1:].split('/'):
        if chunk == '.':
            continue
        elif chunk == '..':
            # parent dir.
            newpath = newpath[:-1]
            continue
        elif _fullmatch(r'\.{3,}', chunk) is not None:
            # parent dir.
            newpath = newpath[:-1]
            continue
        newpath += [chunk]
    return six.moves.urllib.parse.urlunparse(
        parsed[:2] + ('/' + ('/'.join(newpath)), ) + parsed[3:])


def get_swagger_version(obj):
    """ get swagger version from loaded json """

    if isinstance(obj, dict):
        if 'swaggerVersion' in obj:
            return obj['swaggerVersion']
        elif 'swagger' in obj:
            return obj['swagger']
        elif 'openapi' in obj:
            return obj['openapi']
        return None
    else:
        # should be an instance of BaseObj
        return obj.swaggerVersion if hasattr(obj,
                                             'swaggerVersion') else obj.swagger


def _diff_(src, dst, ret=None, jp=None, exclude=[], include=[]):
    """ compare 2 dict/list, return a list containing
    json-pointer indicating what's different, and what's diff exactly.

    - list length diff: (jp, length of src, length of dst)
    - dict key diff: (jp, None, None)
    - when src is dict or list, and dst is not: (jp, type(src), type(dst))
    - other: (jp, src, dst)
    """

    def _dict_(src, dst, ret, jp):
        ss, sd = set(src.keys()), set(dst.keys())
        # what's include is prior to what's exclude
        si, se = set(include or []), set(exclude or [])
        ss, sd = (ss & si, sd & si) if si else (ss, sd)
        ss, sd = (ss - se, sd - se) if se else (ss, sd)

        # added keys
        for k in sd - ss:
            ret.append((
                jp_compose(k, base=jp),
                None,
                None,
            ))

        # removed keys
        for k in ss - sd:
            ret.append((
                jp_compose(k, base=jp),
                None,
                None,
            ))

        # same key
        for k in ss & sd:
            _diff_(src[k], dst[k], ret, jp_compose(k, base=jp), exclude,
                   include)

    def _list_(src, dst, ret, jp):
        if len(src) < len(dst):
            ret.append((
                jp,
                len(src),
                len(dst),
            ))
        elif len(src) > len(dst):
            ret.append((
                jp,
                len(src),
                len(dst),
            ))
        else:
            if len(src) == 0:
                return

            # make sure every element in list is the same
            def r(x, y):
                if type(y) != type(x):
                    raise ValueError('different type: {0}, {1}'.format(
                        type(y).__name__,
                        type(x).__name__))
                return x

            ts = type(functools.reduce(r, src))
            td = type(functools.reduce(r, dst))

            # when type is different
            while True:
                if issubclass(ts, six.string_types) and issubclass(
                        td, six.string_types):
                    break
                if issubclass(ts, six.integer_types) and issubclass(
                        td, six.integer_types):
                    break
                if ts == td:
                    break
                ret.append((
                    jp,
                    str(ts),
                    str(td),
                ))
                return

            if ts != dict:
                ss, sd = sorted(src), sorted(dst)
            else:
                # process dict without sorting
                # TODO: find a way to sort list of dict, (ooch)
                ss, sd = src, dst

            for idx, (s, d) in enumerate(zip(src, dst)):
                _diff_(s, d, ret, jp_compose(str(idx), base=jp), exclude,
                       include)

    ret = [] if ret == None else ret
    jp = '' if jp == None else jp

    if isinstance(src, dict):
        if not isinstance(dst, dict):
            ret.append((
                jp,
                type(src).__name__,
                type(dst).__name__,
            ))
        else:
            _dict_(src, dst, ret, jp)
    elif isinstance(src, list):
        if not isinstance(dst, list):
            ret.append((
                jp,
                type(src).__name__,
                type(dst).__name__,
            ))
        else:
            _list_(src, dst, ret, jp)
    elif src != dst:
        ret.append((
            jp,
            src,
            dst,
        ))

    return ret


def get_or_none(obj, *a):
    ret = obj
    for v in a:
        ret = getattr(ret, v, None)
        if not ret:
            break
    return ret


def patch_path(base_path, path):
    # try to get extension from base_path
    _, ext = os.path.splitext(base_path)
    if ext not in consts.VALID_FILE_EXT:
        ext = ''

    # try to get extension from path
    _, ext = os.path.splitext(path) if ext == '' else (None, ext)
    if ext not in consts.VALID_FILE_EXT:
        ext = ''

    # .json is default extension to try
    ext = '.json' if ext == '' else ext
    # make sure we get .json or .yaml files
    if not path.endswith(ext):
        path = path + ext

    # trim the leading slash, which is invalid on Windows
    if os.name == 'nt' and path.startswith('/'):
        path = path[1:]

    return path


def get_supported_versions(module_name, is_pkg=False):
    versions = [
        name for _, name, pkg in pkgutil.iter_modules(
            [os.path.join(os.path.dirname(__file__), module_name)])
        if pkg == is_pkg
    ]

    # skip every file name that is not started with 'v'
    versions = [name for name in versions if name.startswith('v')]

    # convert v1_2 to 1.2, and sort
    return sorted(
        [v[1:].replace('_', '.') for v in versions],
        key=distutils.version.StrictVersion)
