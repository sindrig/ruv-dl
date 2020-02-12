import os

DATE_FORMAT = '%Y/%m/%d'
DATE_FORMATS = (DATE_FORMAT, '%Y-%m-%d')
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATETIME_FORMATS = (DATETIME_FORMAT, '%Y-%m-%dT%H:%M:%S')
DATE_PART_LENGTH = 4 + 1 + 2 + 1 + 2
URL_TEMPLATE = (
    'http://smooth.ruv.cache.is/{openclose}/{date}/2400kbps/{fn}.mp4'
)


PROGRAM_INFO_FN = 'program_info.json'
NON_SEASON_FIELDS = ('program', '__version__')

CACHE_LOCATION = os.path.join(os.path.expanduser('~'), '.ruvdlcache')
# In case we change the cache setup, change the cache version value and we
# will invalidate all old cache.
CACHE_VERSION_KEY = '__cache_version__'
CACHE_VERSION = '1'

DEFAULT_VIDEO_DESTINATION = os.path.join(os.path.expanduser('~'), 'Videos/ruv')
