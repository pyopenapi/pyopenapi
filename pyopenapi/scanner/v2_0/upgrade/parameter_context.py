from __future__ import absolute_import


class ParameterContext(object):
    """ A parameter object in swagger 2.0 might be converted
    to 'part of' a requestBody of a single parameter object
    in Open API 3.0. It's relatively complex when doing this.

    Need a context object to pass information from top converter
    to lower converter
    """

    def __init__(self, name, is_body=False, is_file=False):
        self.__is_body = is_body
        self.__is_file = is_file
        self.__name = name

    @property
    def is_body(self):
        return self.__is_body

    @property
    def is_file(self):
        return self.__is_file

    @property
    def name(self):
        return self.__name

