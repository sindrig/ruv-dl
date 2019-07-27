#!/usr/bin/env python
import json
import os
import logging

from ruv_dl.constants import CACHE_LOCATION, CACHE_VERSION, CACHE_VERSION_KEY

logger = logging.getLogger(__name__)


class CacheVersionException(Exception):
    pass


class DiskCache:
    def __init__(self, program_id):
        self.location = os.path.join(CACHE_LOCATION, f'{program_id}.json')
        try:
            with open(self.location, 'r') as f:
                self._data = json.loads(f.read())
            SAVED_CACHE_VERSION = self._data.get(CACHE_VERSION_KEY)
            if SAVED_CACHE_VERSION != CACHE_VERSION:
                logger.info(
                    f'Have cache version "{SAVED_CACHE_VERSION}" but '
                    f'want {CACHE_VERSION}. Starting with empty cache.'
                )
                raise CacheVersionException()
            logger.debug('Cache version OK.')
        except (FileNotFoundError, CacheVersionException):
            self._data = {
                CACHE_VERSION_KEY: CACHE_VERSION,
            }

    def get(self, key):
        return self._data[key]

    def set(self, key, data):
        self._data[key] = data

    def has(self, key):
        return key in self._data

    def remove(self, key):
        del self._data[key]

    def write(self):
        with open(self.location, 'w') as f:
            f.write(json.dumps(self._data))
