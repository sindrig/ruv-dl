#!/usr/bin/env python
import itertools
import os
import shutil
import logging
import sys
import click
import multiprocessing
from multiprocessing.pool import ThreadPool

from ruv_dl.runtime import settings
from ruv_dl.programs import ProgramFetcher
from ruv_dl.mover import Mover
from ruv_dl.crawler import Crawler
from ruv_dl.downloader import Downloader
from ruv_dl.migrations import MIGRATIONS
from ruv_dl.constants import DEFAULT_VIDEO_DESTINATION, CACHE_LOCATION


logger = logging.getLogger('ruv_dl')
handler = logging.StreamHandler(sys.stdout)
format_str = '%(asctime)s - %(name)s -  %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter(format_str, date_format)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARN)


@click.group()
@click.option('--dryrun/--no-dryrun', default=False)
@click.option('-v', '--verbosity', count=True)
@click.option('--empty-cache', default=False, is_flag=True)
@click.option(
    '-d',
    '--destination',
    default=DEFAULT_VIDEO_DESTINATION,
    type=click.Path(),
    help='Top level destination directory.',
)
@click.pass_context
def cli(ctx, dryrun, verbosity, empty_cache, destination):
    with settings:
        settings.dryrun = dryrun
    ctx.obj['dryrun'] = dryrun
    ctx.obj['destination'] = destination
    if verbosity is not None:
        multiprocessing_logger = multiprocessing.get_logger()
        if verbosity > 2:
            multiprocessing_logger.addHandler(handler)
            multiprocessing_logger.setLevel(logging.DEBUG)
        if verbosity > 1:
            logger.setLevel(logging.DEBUG)
            multiprocessing_logger.addHandler(handler)
            multiprocessing_logger.setLevel(logging.INFO)
        elif verbosity > 0:
            logger.setLevel(logging.INFO)

    if empty_cache:
        if os.path.exists(CACHE_LOCATION):
            shutil.rmtree(CACHE_LOCATION)
    os.makedirs(CACHE_LOCATION, exist_ok=True)


@cli.command()
@click.argument(
    'query', nargs=-1, type=click.STRING,
)
@click.option(
    '-u',
    '--update',
    default=False,
    is_flag=True,
    help='Search for all saved shows in `--destination` and download '
    'available episodes',
)
@click.option(
    '--days-between-episodes',
    type=click.INT,
    default=7,
    help='Rate of episode release',
)
@click.option(
    '--iteration-count',
    type=click.INT,
    default=5,
    help='Maximum passes to allow for no shows found.',
)
@click.option(
    '--sequential',
    default=False,
    is_flag=True,
    help='Do not run threaded, only download one file at a time.',
)
@click.pass_context
def download(
    ctx, query, update, days_between_episodes, iteration_count, sequential,
):
    '''
        Download ruv programs by searching for query (can specify multiple)
        or update your currently synced programs.
    '''
    destination = ctx.obj['destination']
    if bool(query) == bool(update):
        click.echo(download.get_help(ctx))
        raise click.UsageError(
            'Query terms and update are mutually exclusive and either must '
            'be included'
        )
    os.makedirs(destination, exist_ok=True)
    fetcher = ProgramFetcher(query, update, destination)
    with ThreadPool(8) as pool:
        programs = {}
        for program in fetcher.get_programs():
            logger.info(f'------ {program["title"]} [{program["id"]}] ------')
            crawler = Crawler(
                days_between_episodes=days_between_episodes,
                iteration_count=iteration_count,
                program=program,
            )
            programs[program['id']] = {
                'program': program,
                'episodes': pool.apply_async(crawler.search_for_episodes),
            }

        downloaders = []
        for program_id, data in programs.items():
            downloader = Downloader(
                destination=destination,
                program=data['program'],
                episode_entries=data['episodes'].get(),
                threaded=not sequential,
            )
            entries = downloader.organize()
            downloaders.append((downloader, entries))

    total_entries_to_download = sum(len(entries) for _, entries in downloaders)
    if not total_entries_to_download:
        logger.info('No entries to download, bye')
    else:
        logger.warning(f'Downloading {total_entries_to_download} files...')
        if ctx.obj['dryrun']:
            for downloader, entries in downloaders:
                logger.info(
                    '%s - %s',
                    downloader.program['title'],
                    downloader.program['id'],
                )
                for entry in entries:
                    logger.info('%s: %d', entry, entry.episode.number)
            logger.warning('Dryrun, not downloading anything, bye')
            return
        if sequential:
            results = [
                [downloader.download_file(entry) for entry in entries]
                for downloader, entries in downloaders
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


@cli.command()
@click.argument('migration', type=click.INT)
@click.pass_context
def migrate(ctx, migration):
    for entry in MIGRATIONS[migration]:
        entry(dryrun=ctx.obj['dryrun'], destination=ctx.obj['destination'])


@cli.command()
@click.argument('src', type=click.Path(resolve_path=True, exists=True))
@click.argument('dst', type=click.Path(resolve_path=True))
@click.pass_context
def mv(ctx, src, dst):
    '''
        Move season or episode to a new destination. Only supports moving
        episodes within a season and seasons within programs.
    '''
    Mover(src, dst).move()


def main():
    cli(obj={})
