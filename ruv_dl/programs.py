#!/usr/bin/env python
import json
import os
import logging
import glob

import requests

from ruv_dl.constants import PROGRAM_INFO_FN

logger = logging.getLogger(__name__)


class ProgramFetcher:
    pool = None

    def __init__(self, query, update, destination):
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

    def get_programs_to_update(self):
        for program_info in glob.glob(
            os.path.join(self.destination, '*', PROGRAM_INFO_FN)
        ):
            with open(program_info, 'r') as f:
                try:
                    data = json.loads(f.read())
                except ValueError:
                    logger.info(f'Could not parse {program_info}')
                if 'program' in data:
                    if 'id' in data['program']:
                        yield data['program']
                    else:
                        logger.info(
                            f'Could not get program id from {data["program"]}'
                        )
                else:
                    logger.info(f'Could not get program from {data}')
