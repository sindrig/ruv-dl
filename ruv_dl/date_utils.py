import datetime

from ruv_dl.constants import DATETIME_FORMATS, DATE_FORMATS


def parse_datetime(s, f=DATETIME_FORMATS):
    for d in f:
        try:
            return datetime.datetime.strptime(s, d)
        except ValueError:
            pass
    raise ValueError(f'{s} does not match any format: {f}')


def parse_date(s):
    return parse_datetime(s, DATE_FORMATS)
