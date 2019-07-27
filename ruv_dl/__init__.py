#!/usr/bin/env python
import argparse
import itertools
import os
import shutil
import logging
import sys
import multiprocessing
from multiprocessing.pool import ThreadPool

from ruv_dl.programs import ProgramFetcher
from ruv_dl.crawler import Crawler
from ruv_dl.downloader import Downloader
from ruv_dl.constants import DEFAULT_VIDEO_DESTINATION, CACHE_LOCATION


logger = logging.getLogger('ruv_dl')
handler = logging.StreamHandler(sys.stdout)
format_str = '%(asctime)s - %(name)s -  %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter(format_str, date_format)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARN)


def run(args):
    fetcher = ProgramFetcher(args.query, args.update, args.destination)
    with ThreadPool(8) as pool:
        programs = {}
        for program in fetcher.get_programs():
            logger.info(f'------ {program["title"]} [{program["id"]}] ------')
            crawler = Crawler(
                days_between_episodes=args.days_between_episodes,
                iteration_count=args.iteration_count,
                program=program,
            )
            programs[program['id']] = {
                'program': program,
                'episodes': pool.apply_async(
                    crawler.search_for_episodes
                )
            }

        downloaders = []
        for program_id, data in programs.items():
            downloader = Downloader(
                destination=args.destination,
                program=data['program'],
                episode_entries=data['episodes'].get(),
                threaded=not args.sequential,
            )
            entries = downloader.organize()
            downloaders.append((downloader, entries))

    total_entries_to_download = sum(
        len(entries) for _, entries in downloaders
    )
    if not total_entries_to_download:
        logger.info('No entries to download, bye')
    else:
        logger.warning(f'Downloading {total_entries_to_download} files...')
        if args.dryrun:
            logger.warning('Dryrun, not downloading anything, bye')
            return
        if args.sequential:
            results = [
                [
                    downloader.download_file(entry)
                    for entry in entries
                ] for downloader, entries in downloaders
            ]
        else:
            with ThreadPool(8) as pool:
                pool.__exit__
                async_results = [
                    pool.map_async(downloader.download_file, entries)
                    for downloader, entries in downloaders
                ]
                results = [result.get() for result in async_results]
        logger.warning(
            f'{len([r for r in itertools.chain(*results) if r])} '
            'files downloaded'
        )


def main():
    parser = argparse.ArgumentParser()
    # TODO: Subparser for other stuff and split this up.
    parser.add_argument(
        'action',
        help='Action to run.',
        choices=['download'],
    )
    query_arg = parser.add_argument(
        'query',
        help='Search terms to search for programs.',
        nargs='*',
    )
    parser.add_argument(
        '-u', '--update',
        action='store_true',
        help='Search for all saved shows in `--destination` and download '
        'available episodes'
    )
    parser.add_argument(
        '--destination', default=DEFAULT_VIDEO_DESTINATION, nargs='?',
        type=os.path.abspath,
        help='Top level destination directory.'
    )
    parser.add_argument(
        '--days-between-episodes', type=int, default=7, nargs='?',
        help='Rate of episode release.'
    )
    parser.add_argument(
        '--iteration-count', type=int, default=5, nargs='?',
        help='Maximum days to allow for now shows found.'
    )
    parser.add_argument(
        '--empty-cache',
        action='store_true',
        help='Empty request cache to api.ruv.is before running.'
    )
    parser.add_argument(
        '--sequential',
        action='store_true',
        help='Do not run threaded, only download one file at a time.'
    )
    parser.add_argument(
        '--dryrun',
        action='store_true',
        help='Only search and organize episodes, do not download them.'
    )
    parser.add_argument(
        '-v', '--verbosity', action='count',
        help='Increase output verbosity'
    )
    args = parser.parse_args()
    if bool(args.query) == bool(args.update):
        raise argparse.ArgumentError(
            query_arg,
            'Query terms and update are mutually exclusive and either must '
            'be included'
        )
    if args.verbosity is not None:
        multiprocessing_logger = multiprocessing.get_logger()
        if args.verbosity > 2:
            multiprocessing_logger.addHandler(handler)
            multiprocessing_logger.setLevel(logging.DEBUG)
        if args.verbosity > 1:
            logger.setLevel(logging.DEBUG)
            multiprocessing_logger.addHandler(handler)
            multiprocessing_logger.setLevel(logging.INFO)
        elif args.verbosity > 0:
            logger.setLevel(logging.INFO)
    if args.empty_cache:
        if os.path.exists(CACHE_LOCATION):
            shutil.rmtree(CACHE_LOCATION)
    os.makedirs(args.destination, exist_ok=True)
    os.makedirs(CACHE_LOCATION, exist_ok=True)
    run(args)
