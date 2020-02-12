#!/usr/bin/env python
import datetime
import logging

from urllib.parse import parse_qs, urlparse
import requests

from ruv_dl.cache import DiskCache
from ruv_dl.data import Entry
from ruv_dl.date_utils import parse_datetime, parse_date
from ruv_dl.constants import (
    DATETIME_FORMAT,
    DATE_FORMAT,
    URL_TEMPLATE,
    DATE_PART_LENGTH,
)

logger = logging.getLogger(__name__)


class Crawler:
    def __init__(self, program, iteration_count, days_between_episodes):
        self.program = program
        self.itercount = iteration_count
        self.days_between_episodes = days_between_episodes
        self.prefer_open = True
        self.cache = DiskCache(program['id'])
        logger.debug(
            '\n'.join(
                [
                    'Initializing crawler with:',
                    f'Iteration count: {self.itercount}',
                    f'Days between episodes: {self.days_between_episodes}',
                ]
            )
        )

    def get_entry(self, date, fn, episode=None):
        cache_key = f'{date.strftime(DATE_FORMAT)}-{fn}'
        if not self.cache.has(cache_key):
            r = requests.head(
                URL_TEMPLATE.format(
                    date=date.strftime(DATE_FORMAT),
                    fn=fn,
                    openclose='opid' if self.prefer_open else 'lokad',
                )
            )
            logger.info(
                'Checking %s - %s - %s (is_open: %s)'
                % (date.strftime(DATE_FORMAT), fn, r.ok, self.prefer_open,)
            )
            if r.ok:
                self.cache.set(
                    cache_key,
                    {
                        'success': True,
                        'url': r.url,
                        'etag': r.headers['ETag'],
                        'checked_at': datetime.datetime.now().strftime(
                            DATETIME_FORMAT,
                        ),
                    },
                )
            else:
                self.cache.set(
                    cache_key,
                    {
                        'success': False,
                        'status_code': r.status_code,
                        'checked_at': datetime.datetime.now().strftime(
                            DATETIME_FORMAT,
                        ),
                    },
                )
        info = self.cache.get(cache_key)
        checked_at = parse_datetime(info['checked_at'])
        if info['success']:
            return Entry(
                fn=fn,
                url=info['url'],
                date=date,
                etag=info['etag'],
                episode=episode,
            )
        elif (
            # Don't remove unless we last checked before the show was aired
            checked_at <= (date + datetime.timedelta(1))
            and
            # And we haven't checked this link for over 1 hours
            abs((checked_at - datetime.datetime.now()).total_seconds() / 3600)
            > 1
            and
            # And the show should have been aired
            date <= (datetime.datetime.now() + datetime.timedelta(1))
        ):
            self.cache.remove(cache_key)
            return self.get_entry(date, fn)

    def get_new_fn(self, fn, direction):
        known_delimeters = 'ATSU'
        for delimiter in known_delimeters:
            try:
                fn_id, something = fn.split(delimiter)
            except ValueError:
                continue
            new_id = str(int(fn_id) + direction)
            while len(new_id) < len(fn_id):
                new_id = f'0{new_id}'
            return f'{new_id}{delimiter}{something}'
        else:
            raise RuntimeError(
                f'No known delimiters [{known_delimeters}] found in {fn}'
            )

    def crawl(self, date, fn, direction=1):
        new_fn = self.get_new_fn(fn, direction)
        for i in range(self.itercount):
            # Search for maximum 2 weeks back in time
            date_to_check = date + datetime.timedelta(
                days=i * direction * self.days_between_episodes
            )
            entry = self.get_entry(date_to_check, new_fn,)
            if entry:
                yield entry
                yield from self.crawl(date_to_check, new_fn, direction)
                break

    def search_for_episodes(self):
        files = set()
        episodes = self.program['episodes']
        if not episodes:
            logger.info('No episodes found for %s', self.program['title'])
        for episode in episodes:
            self.prefer_open = 'opid' in episode['file']
            manifest_url = episode['file']
            parts = urlparse(manifest_url)
            query = parse_qs(parts.query)
            wanted_stream = query['streams'][0].split(',')[0]
            # Dates are the first part, '%Y/%m/%d'
            datestr = wanted_stream[:DATE_PART_LENGTH]
            try:
                date = parse_date(datestr)
            except ValueError:
                logger.info(
                    f'Could not parse date {datestr} from {wanted_stream}'
                )
                continue
            fn = wanted_stream.split('/')[-1].split('.')[0]
            first_entry = self.get_entry(date, fn, episode=episode)
            if first_entry:
                files.add(first_entry)
            else:
                expire_date = parse_date(episode['file_expires']).date()
                if expire_date <= datetime.date.today():
                    logger.warning('File %s expired at %s', fn, expire_date)
                else:
                    raise RuntimeError(
                        'Could not get url for first episode...?'
                    )
            logger.debug('Searching backwards in time...')
            for entry in self.crawl(date, fn, direction=-1):
                files.add(entry)
            logger.debug('Searching forward in time...')
            for entry in self.crawl(date, fn, direction=1):
                files.add(entry)
        self.cache.write()
        return files
