from __future__ import absolute_import

def to_external_docs(obj, path):
    ret = {}
    ret['url'] = obj.url
    if obj.description:
        ret['description'] = obj.description

    return ret
