# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging

logger = logging.getLogger(__name__)


def upgrade(obj, _, jref):
    logger.info('upgrade %s to 2.0 spec', jref)

    return obj, {}
