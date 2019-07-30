#!/usr/bin/env python
import json
import os
import logging
import glob

import requests

from ruv_dl.data import Entry, EntrySet
from ruv_dl.constants import PROGRAM_INFO_FN, NON_SEASON_FIELDS

logger = logging.getLogger(__name__)


class ProgramInfo:
    def __init__(self, fn, initialize_empty=False):
        self.fn = fn
        if initialize_empty:
            self._data = {
                '__version__': 1
            }
        else:
            with open(fn, 'r') as f:
                try:
                    data = json.loads(f.read())
                except ValueError:
                    logger.info('Could not parse %s', fn)
                else:
                    if 'program' in data:
                        if 'id' in data['program']:
                            self._data = data
                        else:
                            logger.info(
                                'Could not get program id from %s',
                                data["program"],
                            )
                    else:
                        logger.info('Could not get program from %s', data)

    def __str__(self):
        return f'[{self.fn}: Version {self.version}]'

    @property
    def program(self):
        return self._data['program']

    @program.setter
    def program(self, program):
        self._data['program'] = program

    @property
    def version(self):
        return self._data.get('__version__', 0)

    @version.setter
    def version(self, version):
        self._data['__version__'] = version

    def write(self):
        with open(self.fn, 'w') as f:
            f.write(json.dumps(self._data, indent=4))

    def is_valid(self):
        return hasattr(self, '_data')

    @property
    def seasons(self):
        return {
            key: EntrySet(Entry.from_dict(entry) for entry in entries)
            for key, entries in self._data.items()
            if key not in NON_SEASON_FIELDS
        }

    @seasons.setter
    def seasons(self, seasons):
        keys = list(
            key for key in self._data.keys()
            if key not in NON_SEASON_FIELDS
        )
        for key in keys:
            del self._data[key]
        for key, entries in seasons.items():
            self._data[key] = [entry.to_dict() for entry in entries.sorted()]


class ProgramFetcher:
    pool = None

    def __init__(self, query=None, update=None, destination=None):
        if not destination:
            raise RuntimeError('Missing required destination parameter')
        self.query = query
        self.update = update
        self.destination = destination

    def get_programs(self):
        if self.query:
            return self.get_programs_by_query(self.query)
        return self.get_programs_to_update()

    def get_programs_by_query(self, queries):
        for query in queries:
            if query.isdigit():
                program_id = query
            else:
                program_id = self.get_program_id(query)
            r = requests.get(
                f'https://api.ruv.is/api/programs/program/{program_id}/all'
            )
            if r.ok:
                yield r.json()
            else:
                logger.warning(
                    f'Request for program {program_id} (query {query}) '
                    f'failed with status code {r.status_code}.'
                )

    def get_program_id(self, query):
        r = requests.get(
            f'https://api.ruv.is/api/programs/search/tv/{query}'
        )
        r.raise_for_status()
        programs = r.json()['programs']
        if not programs:
            raise RuntimeError(f'No programs found matching {query}')
        while True:
            for i, program in enumerate(programs):
                print(i + 1, ':', program['title'])
            selection = input('Select program: ')
            if selection.isdigit():
                selection = int(selection)
                if selection > 0 and selection <= len(programs):
                    return programs[selection - 1]['id']

    def get_all_program_infos(self):
        for fn in glob.glob(
            os.path.join(self.destination, '*', PROGRAM_INFO_FN)
        ):
            program_info = ProgramInfo(fn)
            if program_info.is_valid():
                yield program_info

    def get_programs_to_update(self):
        for program_info in self.get_all_program_infos():
            yield program_info.program
