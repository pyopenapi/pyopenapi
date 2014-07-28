from __future__ import absolute_import
import os

def get_test_data_folder(which=""):
    """
    """
    import pyopenapi.tests.data

    folder = os.path.dirname(pyopenapi.tests.data.__file__)
    if which != None:
        folder = os.path.join(folder, which)
    return folder

