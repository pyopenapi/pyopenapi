# -*- coding: utf-8 -*-

from __future__ import absolute_import

BASE_SCHEMA_FIELDS = (
    'type',
    'format',
    'default',
    'maximum',
    'exclusiveMaximum',
    'minimum',
    'exclusiveMinimum',
    'maxLength',
    'minLength',
    'pattern',
    'maxItems',
    'minItems',
    'uniqueItems',
    'enum',
    'multipleOf',
)

SCHEMA_FIELDS = BASE_SCHEMA_FIELDS + (
    'title',
    'maxProperties',
    'minProperties',
    'description',
    'readOnly',
    'writeOnly',
    'example',
)

FILE_CONTENT_TYPES = [
    'multipart/form-data',
    'application/x-www-form-urlencoded',
    'application/octet-stream',
    'application/pdf',
    'image/*',
    'image/gif',
    'image/png',
    'image/jpeg',
    'image/bmp',
    'image/webp',
    'audio/*',
    'audio/midi',
    'audio/mpeg',
    'audio/webm',
    'audio/ogg',
    'audio/wav',
    'video/*',
    'video/webm',
    'video/ogg',
]
