import json
import itertools
import os
import logging
import time

import requests

from ruv_dl.data import Entry
from ruv_dl.constants import PROGRAM_INFO_FN

logger = logging.getLogger(__name__)


class Downloader:
    def __init__(self, destination, program, episode_entries, threaded=True):
        self.destination = destination
        self.program = program
        self.episode_entries = episode_entries
        self.threaded = threaded

    def organize(self):
        logger.info(f'Organizing {self.program["title"]}')
        info_fn = os.path.join(
            self.destination,
            self.program['title'],
            PROGRAM_INFO_FN,
        )
        os.makedirs(os.path.dirname(info_fn), exist_ok=True)
        try:
            with open(info_fn, 'r') as f:
                # We store the program info next to the season episodes
                seasons = {
                    key: {Entry.from_dict(entry) for entry in entries}
                    for key, entries in json.loads(f.read()).items()
                    if key != 'program'
                }
        except FileNotFoundError:
            seasons = {}
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
                seasons[max((seasons or {0: 0}).keys()) + 1] = {entry}
        # Calculate target paths for entries
        for season, entries in seasons.items():
            season_folder = os.path.join(
                self.destination,
                self.program['title'],
                f'Season {season}',
            )
            os.makedirs(season_folder, exist_ok=True)
            for i, entry in enumerate(
                sorted(entries, key=lambda entry: entry.date)
            ):
                fn = (
                    f'{self.program["title"]} - '
                    f'S{str(season).zfill(2)}E{str(i + 1).zfill(2)}.mp4'
                )
                target_path = os.path.join(
                    season_folder,
                    fn,
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
        with open(info_fn, 'w') as f:
            serialized_data = {
                season: [entry.to_dict() for entry in entries]
                for season, entries in seasons.items()
            }
            serialized_data['program'] = self.program
            f.write(json.dumps(serialized_data, indent=4))
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
