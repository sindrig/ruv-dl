import logging
import os
import copy
import shutil

from ruv_dl.programs import ProgramFetcher
from ruv_dl.data import Entry, Episode

logger = logging.getLogger(__name__)

'''
    TODO: Split migrations to seperate files when/if we need more.
          Create some kind of autodiscovery and autopopulation of migrations.
          Also automatically bump version in program_info?
'''


def move_old_locations(destination, dryrun=False):
    fetcher = ProgramFetcher(None, None, destination)
    for program_info in fetcher.get_all_program_infos():
        if program_info.version >= 1:
            logger.info('Skipping %s', program_info)
            continue
        program = program_info.program
        logger.info('Targeting %s', program['title'])
        seasons = program_info.seasons
        # {current_path: new_path}
        files_to_move = {}
        for season, entries in seasons.items():
            season_folder = Entry.get_season_folder(
                destination, program, season
            )
            for i, target_entry in enumerate(entries.sorted()):
                if target_entry.episode.number is None:
                    raise RuntimeError(
                        'You need to attempt sync for this program once '
                        'before running this migration.'
                    )
                src_entry = copy.deepcopy(target_entry)
                src_entry.episode = Episode(None)
                src_entry.episode.number = i + 1

                src_dest = os.path.join(
                    season_folder,
                    src_entry.get_target_basename(program, season),
                )

                target_dest = os.path.join(
                    season_folder,
                    target_entry.get_target_basename(program, season),
                )

                if os.path.isfile(src_dest):
                    files_to_move[src_dest] = target_dest
        if dryrun:
            logger.warning('Running with dryrun, no change to filesystem')
            for current, target in files_to_move.items():
                logger.info('Would move %s to %s', current, target)
        else:
            for current, target in files_to_move.items():
                os.makedirs(os.path.dirname(target), exist_ok=True)
                logger.info('Moving %s to %s', current, target)
                shutil.move(current, target)
            program_info.version = 1
            program_info.write()


MIGRATIONS = {
    1: (move_old_locations, )
}
