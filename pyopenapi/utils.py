# -*- coding: utf-8 -*-
from __future__ import absolute_import
import sys
import re
import os
import functools
import pkgutil
import distutils
import six
from . import consts
from .errs import CycleDetectionError


#TODO: accept varg
def scope_compose(scope, name, sep=consts.SCOPE_SEPARATOR):
    """ compose a new scope

    :param str scope: current scope
    :param str name: name of next level in scope
    :return the composed scope
    """

    if name is None:
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
            for obj_name in self.keys():
                if obj_name.endswith(k):
                    ret.append(obj_name)
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


def jp_compose(segment, base=None):
    """ append/encode a string to json-pointer
    """
    if segment is None:
        return base

    segments = [segment] if isinstance(segment, six.string_types) else segment
    segments = [x.replace('~', '~0').replace('/', '~1') for x in segments]
    if base:
        segments.insert(0, base)
    return '/'.join(segments)


def jp_split(jp, max_split=-1):
    """ split/decode a string from json-pointer
    """
    if jp == '' or jp is None:
        return []

    def _decode(x):
        x = x.replace('~1', '/')
        return x.replace('~0', '~')

    return [_decode(x) for x in jp.split('/', max_split)]


def jr_split(json_ref):
    """ split a json-reference into (url, json-pointer)
    """
    parsed = six.moves.urllib.parse.urlparse(json_ref)
    return (normalize_url(
        six.moves.urllib.parse.urlunparse(parsed[:5] + ('', ))),
            '#' + parsed.fragment if parsed.fragment else '#')


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


def path2url(path_part):
    """ Return file:// URL from a filename.
    """
    if sys.version_info.major >= 3 and sys.version_info.minor >= 4:
        import pathlib
        return pathlib.Path(path_part).as_uri()

    return six.moves.urllib.parse.urljoin(
        'file:', six.moves.urllib.request.pathname2url(path_part))


_WINDOWS_PATH_PREFIX_PATTERN = re.compile(r'(^[A-Za-z]:\\)')


def normalize_url(url):
    """ Normalize url
    """
    if not url:
        return url

    matched = _WINDOWS_PATH_PREFIX_PATTERN.match(url)
    if matched:
        return path2url(url)

    parsed = six.moves.urllib.parse.urlparse(url)
    if parsed.scheme == '':
        if parsed.netloc == '' and parsed.path != '':
            # it should be a file path
            url = path2url(os.path.abspath(url))
        else:
            raise ValueError('url should be a http-url or file path -- ' + url)

    return url


def url_dirname(url):
    """ Return the folder containing the '.json' file
    """
    parsed = six.moves.urllib.parse.urlparse(url)
    for ext in [consts.FILE_EXT_JSON, consts.FILE_EXT_YAML]:
        if parsed.path.endswith(ext):
            return six.moves.urllib.parse.urlunparse(
                parsed[:2] + (os.path.dirname(parsed.path), ) + parsed[3:])
    return url


def url_join(url, base_name):
    """ url version of os.path.join
    """
    parsed = six.moves.urllib.parse.urlparse(url)

    new_path = None
    if parsed.path and parsed.path[-1] == '/':
        if base_name and base_name[0] == '/':
            base_name = base_name[1:]  # trim the first character
        new_path = ''.join([parsed.path, base_name])
    else:
        new_path = ('' if base_name and base_name[0] == '/' else
                    '/').join([parsed.path, base_name])

    return six.moves.urllib.parse.urlunparse(parsed[:2] + (
        new_path, ) +  # os.sep is different on windows, don't use it here.
                                             parsed[3:])


def normalize_jr(json_ref, url=None):
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

    if json_ref is None:
        return None

    idx = json_ref.find('#')
    url_part, jp = (json_ref[:idx],
                    json_ref[idx + 1:]) if idx != -1 else (json_ref, None)

    if url_part:
        parsed = six.moves.urllib.parse.urlparse(url_part)
        if parsed.scheme == '' and url:
            url_parsed = six.moves.urllib.parse.urlparse(url)
            # it's the path of relative file
            url_part = six.moves.urllib.parse.urlunparse(
                url_parsed[:2] +
                ('/'.join([os.path.dirname(url_parsed.path), url_part]),
                 ) + url_parsed[3:])
            url_part = derelativise_url(url_part)
    else:
        url_part = url

    if url_part:
        return ''.join([url_part, '#', jp]) if jp else url_part
    return '#' + jp


def _fullmatch(regex, chunk):
    matched = re.match(regex, chunk)
    if matched and matched.span()[1] == len(chunk):
        return matched
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


def compare_container(src,
                      dst,
                      ret=None,
                      base_path=None,
                      exclude=None,
                      include=None):
    """ compare 2 dict/list, return a list containing
    json-pointer indicating what's different, and what's diff exactly.

    - list length diff: (base_path, length of src, length of dst)
    - dict key diff: (path, None, None)
    - when src is dict or list, and dst is not: (base_path, type(src), type(dst))
    - other: (base_path, src, dst)
    """

    exclude = exclude or []
    include = include or []

    def _dict_(src, dst, ret, base_path):
        set_src, set_dst = set(src.keys()), set(dst.keys())
        # what's include is prior to what's exclude
        set_include, set_exclude = set(include or []), set(exclude or [])
        set_src, set_dst = (set_src & set_include,
                            set_dst & set_include) if set_include else (set_src,
                                                                        set_dst)
        set_src, set_dst = (set_src - set_exclude,
                            set_dst - set_exclude) if set_exclude else (set_src,
                                                                        set_dst)

        # added keys
        for k in set_dst - set_src:
            ret.append((
                jp_compose(k, base=base_path),
                None,
                None,
            ))

        # removed keys
        for k in set_src - set_dst:
            ret.append((
                jp_compose(k, base=base_path),
                None,
                None,
            ))

        # same key
        for k in set_src & set_dst:
            compare_container(src[k], dst[k], ret, jp_compose(
                k, base=base_path), exclude, include)

    def _list_(src, dst, ret, base_path):
        if len(src) < len(dst):
            ret.append((
                base_path,
                len(src),
                len(dst),
            ))
        elif len(src) > len(dst):
            ret.append((
                base_path,
                len(src),
                len(dst),
            ))
        else:
            if not src:
                return

            # make sure every element in list is the same
            def is_singular(x, y):
                # pylint: disable=unidiomatic-typecheck
                if type(y) is not type(x):
                    raise ValueError('different type: {0}, {1}'.format(
                        type(y).__name__,
                        type(x).__name__))
                return x

            type_src = type(functools.reduce(is_singular, src))
            type_dst = type(functools.reduce(is_singular, dst))

            # when type is different
            while True:
                if issubclass(type_src, six.string_types) and issubclass(
                        type_dst, six.string_types):
                    break
                if issubclass(type_src, six.integer_types) and issubclass(
                        type_dst, six.integer_types):
                    break
                if type_src == type_dst:
                    break
                ret.append((
                    base_path,
                    str(type_src),
                    str(type_dst),
                ))
                return

            if type_src != dict:
                sorted_src, sorted_dst = sorted(src), sorted(dst)
            else:
                # process dict without sorting
                # TODO: find a way to sort list of dict, (ooch)
                sorted_src, sorted_dst = src, dst

            for idx, (x, y) in enumerate(zip(sorted_src, sorted_dst)):
                compare_container(x, y, ret, jp_compose(
                    str(idx), base=base_path), exclude, include)

    ret = [] if ret is None else ret
    base_path = '' if base_path is None else base_path

    if isinstance(src, dict):
        if not isinstance(dst, dict):
            ret.append((
                base_path,
                type(src).__name__,
                type(dst).__name__,
            ))
        else:
            _dict_(src, dst, ret, base_path)
    elif isinstance(src, list):
        if not isinstance(dst, list):
            ret.append((
                base_path,
                type(src).__name__,
                type(dst).__name__,
            ))
        else:
            _list_(src, dst, ret, base_path)
    elif src != dst:
        ret.append((
            base_path,
            src,
            dst,
        ))

    return ret


def get_or_none(obj, *args):
    ret = obj
    for x in args:
        ret = getattr(ret, x, None)
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

        # pylint: disable=no-member
        key=distutils.version.StrictVersion)
