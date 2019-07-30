#!/usr/bin/env python
import os
import datetime
import logging

from ruv_dl.constants import DATE_FORMAT

logger = logging.getLogger(__name__)


class Episode:
    def __init__(self, data):
        self.data = data or {}
        self.id = self.data.get('id', None)

    @property
    def number(self):
        return self.data.get('number', None)

    @number.setter
    def number(self, number):
        self.data['number'] = number

    def to_dict(self):
        return self.data


class Entry:
    def __init__(
        self, fn, url, date, etag, episode=None
    ):
        self.fn = fn
        self.url = url
        self.date = date
        self.etag = etag
        self.episode = Episode(episode)
        self.target_path = None

    def to_dict(self):
        return {
            'fn': self.fn,
            'url': self.url,
            'date': self.date.strftime(DATE_FORMAT),
            'etag': self.etag,
            'episode': self.episode.to_dict(),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            fn=data['fn'],
            url=data['url'],
            date=datetime.datetime.strptime(data['date'], DATE_FORMAT),
            etag=data['etag'],
            episode=data.get('episode'),
        )

    def get_target_basename(self, program, season):
        return (
            f'{program["title"]} - '
            f'S{str(season).zfill(2)}E{str(self.episode.number).zfill(2)}.mp4'
        )

    @classmethod
    def get_season_folder(cls, destination, program, season):
        return os.path.join(
            destination,
            program['title'],
            f'Season {season}',
        )

    def set_target_path(self, path):
        # TODO: Get rid of this maybe
        self.target_path = path

    def exists_on_disk(self):
        if self.target_path is None:
            raise RuntimeError(f'Missing target path for {self.to_dict}')
        return os.path.exists(self.target_path)

    def __hash__(self):
        return hash(self.etag)

    def __eq__(self, other):
        return isinstance(other, Entry) and hash(self) == hash(other)

    def __str__(self):
        return f'{self.fn} - {self.date}'


class EntrySet(set):
    def add(self, item):
        for member in self:
            if member == item:
                # If we have the same item twice, we want the one with a full
                # episode entry, if available, chosen.
                item = self._choose_best_item(item, member)
                self.remove(member)
                break
        super().add(item)

    def sorted(self):
        return sorted(self, key=lambda entry: entry.date)

    @classmethod
    def find_target_number(cls, entries, i):
        '''
            Find a target number for entries[i] wrt entries
        '''
        for k in range(0, len(entries)):
            if entries[k].episode and entries[k].episode.id:
                target = entries[k].episode.number + i - k
                logger.info(
                    'Found related episode in %d for %d: %s, '
                    'target number is %d',
                    k,
                    i,
                    entries[i],
                    target
                )
                return target

    def _choose_best_item(self, item, member):
        if item.episode and item.episode.id:
            return item
        elif member.episode:
            return member
        return item

    def __getitem__(self, i):
        return self.sorted()[i]
