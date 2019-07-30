import itertools
import os
import logging
import time

import requests

from ruv_dl.data import Entry, EntrySet
from ruv_dl.programs import ProgramInfo
from ruv_dl.constants import PROGRAM_INFO_FN
from ruv_dl.migrations import MIGRATIONS

logger = logging.getLogger(__name__)
PROGRAM_INFO_VERSION = max(MIGRATIONS.keys())


class Downloader:
    def __init__(self, destination, program, episode_entries, threaded=True):
        self.destination = destination
        self.program = program
        self.episode_entries = episode_entries
        self.threaded = threaded

    def organize(self):
        # TODO: Use ProgramInfo class
        logger.info(f'Organizing {self.program["title"]}')
        info_fn = os.path.join(
            self.destination,
            self.program['title'],
            PROGRAM_INFO_FN,
        )
        os.makedirs(os.path.dirname(info_fn), exist_ok=True)
        try:
            program_info = ProgramInfo(info_fn)
        except FileNotFoundError:
            program_info = ProgramInfo(info_fn, initialize_empty=True)
        seasons = program_info.seasons
        program_info.program = self.program
        # seasons = {
        #     1: {entry, entry, entry},
        #     2: {entry, entry, entry},
        # }
        # Sort episodes into seasons
        for entry in sorted(
            self.episode_entries,
            key=lambda entry: entry.date
        ):
            for season in seasons.keys():
                if any(
                    abs((e.date - entry.date).days) < 10
                    for e in seasons[season]
                ):
                    seasons[season].add(entry)
                    break
            else:
                season = max((seasons or {0: 0}).keys()) + 1
                seasons[season] = EntrySet([entry])
        # Calculate target paths for entries
        for season, entries in seasons.items():
            season_folder = Entry.get_season_folder(
                self.destination, self.program, season
            )
            os.makedirs(season_folder, exist_ok=True)
            for i, entry in enumerate(entries.sorted()):
                if not entry.episode.number:
                    entry.episode.number = EntrySet.find_target_number(
                        entries, i
                    )
                basename = entry.get_target_basename(
                    self.program,
                    season,
                )
                target_path = os.path.join(
                    season_folder,
                    basename,
                )
                entry.set_target_path(target_path)
        # Finally, make sure we don't have the same etag multiple times,
        # prefer the first one in chronological order
        found_etags = []
        for season, entries in seasons.items():
            for entry in [
                entry for entry in entries if entry.etag in found_etags
            ]:
                entries.remove(entry)
            found_etags += [entry.etag for entry in entries]

        program_info.seasons = seasons
        program_info.write()

        missing_migrations = range(
            program_info.version,
            PROGRAM_INFO_VERSION,
        )
        for migration_entry in missing_migrations:
            logger.error(
                'Missing migration %d. Run `ruv-dl migrate %d`. You can '
                'supply `--dryrun` (e.g. `ruv-dl --dryrun migrate ...`) to '
                'see what will be done.',
                migration_entry + 1,
                migration_entry + 1,
            )
        if missing_migrations:
            return []

        return [
            entry
            for entry in itertools.chain(*seasons.values())
            if not entry.exists_on_disk()
        ]

    def download_file(self, entry):
        if os.path.exists(entry.target_path):
            logger.info(
                f'Skipping {entry.target_path} - {entry.url} because '
                'it already exists.'
            )
            return False
        else:
            logger.warning(f'Downloading {entry.url} to {entry.target_path}')

        r = requests.get(entry.url, stream=True)

        if r.ok:
            start = time.time()
            total_length = int(r.headers.get('content-length'))
            dl = 0
            perc_done = 0
            with open(entry.target_path, 'wb') as f:
                for chunk in r:
                    dl += len(chunk)
                    current = int(dl * 10 / total_length)
                    if current > perc_done:
                        perc_done = current
                        logger.info(
                            f'{os.path.basename(entry.target_path)} '
                            f'{perc_done * 10}% '
                            f'({int(dl//(time.time() - start)/1024)}kbps)'
                        )
                    f.write(chunk)

            size = int(os.path.getsize(entry.target_path) / 1024**2)
            logger.warning(
                f'{entry.target_path} ({size}MB) '
                f'downloaded in {int(time.time() - start)}s!'
            )
            return True
        logger.warning(f'Error {r.status_code} for {entry.url}')
        return False
