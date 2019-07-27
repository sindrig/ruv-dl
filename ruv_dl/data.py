#!/usr/bin/env python
import os
import datetime

from ruv_dl.constants import DATE_FORMAT


class Entry:
    def __init__(self, fn, url, date, etag):
        self.fn = fn
        self.url = url
        self.date = date
        self.etag = etag
        self.target_path = None

    def to_dict(self):
        return {
            'fn': self.fn,
            'url': self.url,
            'date': self.date.strftime(DATE_FORMAT),
            'etag': self.etag,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            fn=data['fn'],
            url=data['url'],
            date=datetime.datetime.strptime(data['date'], DATE_FORMAT),
            etag=data['etag'],
        )

    def set_target_path(self, path):
        self.target_path = path

    def exists_on_disk(self):
        if self.target_path is None:
            raise RuntimeError(f'Missing target path for {self.to_dict}')
        return os.path.exists(self.target_path)

    def __hash__(self):
        return hash(self.etag)
        # return hash((self.fn, self.url, self.date, self.etag))

    def __eq__(self, other):
        return isinstance(other, Entry) and hash(self) == hash(other)
