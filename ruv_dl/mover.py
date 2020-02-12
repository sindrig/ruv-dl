#!/usr/bin/env python
import os
import re
import logging
import shutil

from ruv_dl.programs import ProgramInfo
from ruv_dl.runtime import settings
from ruv_dl.exceptions import NamingSchemaError, ProgramInfoError


SEASON_RE = re.compile(f'^Season (\\d+)$')
logger = logging.getLogger(__name__)


class Mover:
    def __init__(self, src, dst):
        for path in (src, dst):
            if not os.path.isabs(path):
                raise OSError(
                    f'Must pass in absolute path - "{path}" is relative.'
                )
        if os.path.exists(dst):
            raise FileExistsError(f'{dst} exists')
        dirname = os.path.dirname(src)
        while dirname != os.path.dirname(dirname):
            try:
                self.program_info = ProgramInfo(dirname)
                break
            except FileNotFoundError:
                dirname = os.path.dirname(dirname)
        else:
            raise FileNotFoundError(
                f'Could not find program info related to {src}'
            )
        self.src = src
        self.dst = dst

    def move(self):
        if os.path.isdir(self.src):
            self.move_season()
        else:
            self.move_episode()

    def move_episode(self):
        src_season, src_episode = self._get_episode_season_and_number(
            self.program_info.program, self.src
        )
        dst_season, dst_episode = self._get_episode_season_and_number(
            self.program_info.program, self.dst
        )
        if dst_season != src_season:
            raise RuntimeError(
                'Moving episodes between seasons is not supported'
            )
        season_number = self._get_season_number(os.path.dirname(self.src))
        seasons = self.program_info.seasons
        season = seasons[season_number]
        src_entry = None
        for entry in season:
            if entry.episode.number == src_episode:
                if src_entry:
                    raise ProgramInfoError(
                        'Found two entries with same number in program info.'
                    )
                src_entry = entry
            if entry.episode.number == dst_episode:
                raise ProgramInfoError(
                    'Destination episode found in program info file.'
                )
        if not src_entry:
            raise ProgramInfoError(
                'Source episode not found in program info file'
            )
        if settings.dryrun:
            logger.warning(f'Dryrun. Would move {self.src} to {self.dst}.')
        else:
            shutil.move(self.src, self.dst)
            src_entry.episode.number = dst_episode
            self.program_info.seasons = seasons
            self.program_info.write()

    def move_season(self):
        seasons = self.program_info.seasons
        src_season_no = self._get_season_number(self.src)
        dst_season_no = self._get_season_number(self.dst)
        if src_season_no not in seasons:
            raise ProgramInfoError(
                f'Source season number {src_season_no} not found in info file '
                f'{self.program_info.fn}'
            )
        files_in_src = os.listdir(self.src)
        filenames_to_move = []
        for fn in files_in_src:
            src = os.path.join(self.src, fn)
            season, episode = self._get_episode_season_and_number(
                self.program_info.program, src
            )
            part_change = f'S{str(season).zfill(2)}'
            assert part_change in src
            dst = src.replace(part_change, f'S{str(dst_season_no).zfill(2)}')
            filenames_to_move.append((src, dst))
        if settings.dryrun:
            logger.warning(f'Dryrun. Would move {self.src} to {self.dst}.')
            for src, dst in filenames_to_move:
                logger.warning(
                    f'Would also move {src} to {dst} prior to moving season'
                )
        else:
            for src, dst in filenames_to_move:
                shutil.move(src, dst)
            shutil.move(self.src, self.dst)
            seasons[dst_season_no] = seasons[src_season_no]
            del seasons[src_season_no]
            self.program_info.seasons = seasons
            self.program_info.write()

    def _get_season_number(self, path):
        name = os.path.basename(path)
        result = SEASON_RE.search(name)
        if not result:
            raise NamingSchemaError(
                f'Season number not determined from {path}'
            )
        return int(result.group(1))

    def _get_episode_re(self, program):
        return re.compile(
            f'Season (\\d+){os.sep}{program["title"]} - S(\\d+)E(\\d+).mp4$'
        )

    def _get_episode_season_and_number(self, program, path):
        result = self._get_episode_re(program).search(path)
        if result:
            season1, season2, episode = result.groups()
            if int(season1) == int(season2):
                return int(season1), int(episode)
            raise NamingSchemaError(
                f'Season number in folder and filename differ in "{path}"'
            )
        raise NamingSchemaError(
            f'Episode/season number not determined from {path}'
        )
