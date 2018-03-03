from __future__ import absolute_import
from pyopenapi.migration.base import ApiBase
from pyopenapi.migration import utils, consts
import os
import six

def get_test_data_folder(version='1.2', which=''):
    """
    """
    import pyopenapi.tests.data

    version = 'v' + version.replace('.', '_')
    folder = os.path.dirname(os.path.abspath(pyopenapi.tests.data.__file__))
    folder = os.path.join(os.path.join(folder, version), which)
    return folder

def get_test_file(version, which, file_name):
    with open(os.path.join(get_test_data_folder(version, which), file_name), 'r') as f:
        return f.read()


class DictDB(dict):
    """ Simple DB for singular model """
    def __init__(self):
        self._db = []

    def create_(self, **data):
        if len([elm for elm in self._db if elm['id'] == data['id']]):
            return False

        self._db.append(data)
        return True

    def read_(self, key):
        found = [elm for elm in self._db if elm['id'] == key]
        if len(found):
            return found[0]
        return None

    def update_(self, **data):
        for elm in self._db:
            if elm['id'] == data['id']:
                elm.update(data)
                return True
        return False

    def delete_(self, key):
        residual = [elm for elm in self._db if elm['id'] != key]
        found, self._db = (len(self._db) > len(residual)), residual
        return found

pet_Tom = dict(id=1, category=dict(id=1, name='dog'), name='Tom',  tags=[dict(id=2, name='yellow'), dict(id=3, name='big')], status='sold')
pet_Mary = dict(id=2, category=dict(id=2, name='cat'), name='Mary', tags=[dict(id=1, name='white'), dict(id=4, name='small')], status='pending')
pet_John = dict(id=3, category=dict(id=2, name='cat'), name='John', tags=[dict(id=2, name='yellow'), dict(id=4, name='small')], status='available')
pet_Sue = dict(id=4, category=dict(id=3, name='fish'), name='Sue', tags=[dict(id=5, name='gold'), dict(id=4, name='small')], status='available')

def create_pet_db():
    pet = DictDB()
    pet.create_(**pet_Tom)
    pet.create_(**pet_Mary)
    pet.create_(**pet_John)
    pet.create_(**pet_Sue)

    return pet

def gen_test_folder_hook(folder):
    def _hook(url):
        p = six.moves.urllib.parse.urlparse(url)
        if p.scheme != 'file':
            return url

        path = os.path.join(folder, p.path if not p.path.startswith('/') else p.path[1:])
        return six.moves.urllib.parse.urlunparse(p[:2]+(path,)+p[3:])

    return _hook

class SampleApp(ApiBase):
    """ app for test
    """

    def __init__(self, url, url_load_hook, resolver, sep):
        super(SampleApp, self).__init__(
            url,
            url_load_hook=url_load_hook,
            resolver=resolver,
            sep=sep
        )

        self.raw = None
        self.root = None

    def prepare_obj(self, obj, jref):
        return obj

    @classmethod
    def load(kls, url, url_load_hook=None, resolver=None, getter=None, sep=consts.SCOPE_SEPARATOR):
        url = utils.normalize_url(url)
        app = kls(url, url_load_hook, resolver, sep)

        app.raw = app.load_obj(url, getter=getter)
        return app

    @classmethod
    def create(kls, url, to_spec_version, url_load_hook=None, resolver=None, getter=None, sep=consts.SCOPE_SEPARATOR):
        url = utils.normalize_url(url)
        app = kls.load(url, url_load_hook=url_load_hook, resolver=resolver, getter=getter, sep=sep)
        app.root = app.migrate_obj(app.raw, url, to_spec_version)

        return app

