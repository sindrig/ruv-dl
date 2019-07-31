import logging
import tempfile
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
        files_to_move = []
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

                if src_dest != target_dest and os.path.isfile(src_dest):
                    files_to_move.append((src_dest, target_dest))
        while files_to_move:
            i = 0
            src_dest, target_dest = files_to_move.pop(0)
            if dryrun:
                logger.info('Would move %s to %s', src_dest, target_dest)
            elif os.path.isfile(target_dest):
                temp_path = next(tempfile._get_candidate_names())
                temp_path = os.path.join(
                    os.path.dirname(target_dest),
                    temp_path,
                )
                logger.info(
                    '%s exists. Moving temporarily to %s and postponing',
                    target_dest, temp_path,
                )
                shutil.move(src_dest, temp_path)
                files_to_move.append((temp_path, target_dest))
            else:
                os.makedirs(os.path.dirname(target_dest), exist_ok=True)
                logger.info('Moving %s to %s', src_dest, target_dest)
                shutil.move(src_dest, target_dest)

        if not dryrun:
            program_info.version = 1
            program_info.write()


MIGRATIONS = {
    1: (move_old_locations, )
}
