from __future__ import absolute_import
from ...scan import Dispatcher
from ...spec.v2_0.objects import PathItem, Operation, Schema, Swagger
from ...spec.v2_0.parser import PathItemContext
from ...utils import jp_split, scope_split, final
import six
import copy


class PatchObject(object):
    """
    - produces/consumes in Operation object should override those in Swagger object.
    - parameters in Operation object should override those in PathItem object.
    - fulfill Operation.method, which is a pyopenapi-only field.
    """

    class Disp(Dispatcher): pass

    def __init__(self, swagger):
        self._swagger = swagger

    @Disp.register([Operation])
    def _operation(self, path, obj, app):
        """
        """
        if isinstance(self._swagger, Swagger):
            # produces/consumes
            obj.update_field('produces', self._swagger.produces if len(obj.produces) == 0 else obj.produces)
            obj.update_field('consumes', self._swagger.consumes if len(obj.consumes) == 0 else obj.consumes)

        # combine parameters from PathItem
        if obj._parent_:
            if obj.parameters:
                for p in obj._parent_.parameters:
                    p_final = final(p)
                    for pp in obj.parameters:
                        if p_final.name == final(pp).name:
                            break
                    else:
                        obj.parameters.append(p)
            else:
                obj.update_field('parameters', copy.copy(obj._parent_.parameters))

        # schemes
        if obj.schemes:
            obj.update_field('cached_schemes', obj.schemes)
        elif isinstance(self._swagger, Swagger):
            obj.update_field('cached_schemes', app.schemes if not self._swagger.schemes else self._swagger.schemes)
        else:
            obj.update_field('cached_schemes', app.schemes)

        # primitive factory
        setattr(obj, '_prim_factory', app.prim_factory)

        # inherit service-wide security requirements
        if obj.security == None and isinstance(self._swagger, Swagger):
            obj.update_field('security', self._swagger.security)

        # mime_codec
        setattr(obj, '_mime_codec', app.mime_codec)

    @Disp.register([PathItem])
    def _path_item(self, path, obj, app):
        """
        """
        k = jp_split(path)[-1] # key to the dict containing PathItem(s)
        if isinstance(self._swagger, Swagger):
            host = self._swagger.host if self._swagger.host else six.moves.urllib.parse.urlparse(app.url)[1]
            host = host if len(host) > 0 else 'localhost'
            url = six.moves.urllib.parse.urlunparse((
                    '',                            # schema
                    host,                          # netloc
                    (self._swagger.basePath or '') + k, # path
                    '', '', '',                    # param, query, fragment
            ))
            base_path = self._swagger.basePath
        else:
            url = None
            base_path = None

        for n in six.iterkeys(PathItemContext.__swagger_child__):
            o = getattr(obj, n)
            if isinstance(o, Operation):
                # base path
                o.update_field('base_path', base_path)
                # path
                o.update_field('path', k)
                # url
                o.update_field('url', url)
                # http method
                o.update_field('method', n)

    @Disp.register([Schema])
    def _schema(self, path, obj, app):
        """ fulfill 'name' field for objects under
        '#/definitions' and with 'properties'
        """
        if path.startswith('#/definitions'):
            last_token = jp_split(path)[-1]
            if app.version == '1.2':
                obj.update_field('name', scope_split(last_token)[-1])
            else:
                obj.update_field('name', last_token)

