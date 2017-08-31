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


