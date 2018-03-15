# -*- coding: utf-8 -*-

from __future__ import absolute_import
from .constants import FILE_CONTENT_TYPES


class ParameterContext(object):
    """ A parameter object in swagger 2.0 might be converted
    to 'part of' a requestBody of a single parameter object
    in Open API 3.0. It's relatively complex when doing this.

    Need a context object to pass information from top converter
    to lower converter
    """

    def __init__(self, name, consumes=None):
        self.__is_body = False
        self.__is_file = False
        self.__is_form = False
        self.__name = name
        self.__valid_mime_types = consumes or []

    @property
    def is_body(self):
        return self.__is_body

    @property
    def is_file(self):
        return self.__is_file

    @property
    def is_form(self):
        return self.__is_form

    def update(self, is_file=False, is_body=False, is_form=False):
        self.__is_file = is_file
        self.__is_body = is_body
        self.__is_form = is_form

    @property
    def name(self):
        return self.__name

    def get_valid_mime_type(self):
        if not self.__valid_mime_types:
            return [self.get_default_mime_type()]

        if self.is_file:
            return list(set(self.__valid_mime_types) & set(FILE_CONTENT_TYPES)
                        ) or [self.get_default_mime_type()]
        elif self.is_form:
            return list(
                set(self.__valid_mime_types) & set([
                    'application/x-www-form-urlencoded', 'multipart/form-data'
                ])) or [self.get_default_mime_type()]
        return self.__valid_mime_types

    def get_default_mime_type(self):
        if self.is_file:
            return 'multipart/form-data'
        elif self.is_form:
            return 'application/x-www-form-urlencoded'
        elif self.is_body:
            return 'application/json'
        return 'text/plain'
