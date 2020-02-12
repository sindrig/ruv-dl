import pytest
import os
import datetime

from ruv_dl.data import EntrySet, Entry
from ruv_dl.programs import ProgramInfo
from ruv_dl.mover import Mover
from ruv_dl.exceptions import NamingSchemaError, ProgramInfoError


def create_program_info(location='/tv/Program', seasons=None):
    pi = ProgramInfo(location, initialize_empty=True)
    pi.program = {'id': 'some-id', 'title': 'Program'}
    pi.seasons = {
        key: EntrySet(
            [
                Entry(
                    '',
                    '',
                    datetime.datetime(2020, 1, 10),
                    f'e{number}',
                    episode={'number': number},
                )
                for number in value
            ]
        )
        for key, value in (seasons or {}).items()
    }
    pi.write()
    return pi


def test_src_must_exist(fs):
    with pytest.raises(FileNotFoundError):
        Mover('/not/exists/', '/no/matter').move()


def test_cannot_move_to_destination_if_exists(fs):
    with open('/src', 'w') as f:
        f.write('contents')
    with open('/dst', 'w') as f:
        f.write('contents2')
    with pytest.raises(FileExistsError):
        Mover('/src', '/dst')


def test_src_and_dst_must_differ(fs):
    # This is essentially covered but I want to be explicit
    with open('/src', 'w') as f:
        f.write('contents')
    with pytest.raises(FileExistsError):
        Mover('/src', '/src')


def test_raises_if_no_program_info_found(fs):
    os.makedirs('/tv/Program/Source')
    os.chdir('/tv/Program')
    with pytest.raises(FileNotFoundError) as e:
        Mover('/tv/Program/Source', '/tv/Program/Destination')
    assert 'Could not find program info related to' in str(e.value)


def test_requires_absolute_path_to_move(fs):
    expected_error = (
        'Must pass in absolute path - "relative/path/here.mp4" is relative.'
    )
    with pytest.raises(OSError) as e:
        Mover('relative/path/here.mp4', '/absolute/path')
    assert str(e.value) == expected_error
    with pytest.raises(OSError) as e:
        Mover('/absolute/path', 'relative/path/here.mp4')
    assert str(e.value) == expected_error


def test_move_season_requires_correct_naming_schema(fs):
    os.makedirs('/tv/Program/Season')
    create_program_info()
    with pytest.raises(NamingSchemaError) as e:
        Mover('/tv/Program/Season', '/tv/Program/Season 2').move()
    expected_error = 'Season number not determined from /tv/Program/Season'
    assert str(e.value) == expected_error

    os.makedirs('/tv/Program/Season 1')
    with pytest.raises(NamingSchemaError) as e:
        Mover('/tv/Program/Season 1', '/tv/Program/Season something').move()
    expected_error = (
        'Season number not determined from /tv/Program/Season something'
    )
    assert str(e.value) == expected_error

    with pytest.raises(ProgramInfoError) as e:
        Mover('/tv/Program/Season 1', '/tv/Program/Season 2').move()
    expected_error = 'Source season number 1 not found in info file'
    assert str(e.value).startswith(expected_error)


def test_move_seasons_fails_if_any_episode_in_src_is_wrong_name_schema(fs):
    os.makedirs('/tv/Program/Season 1')
    create_program_info(seasons={1: [1]})
    os.chdir('/tv/Program')
    with open('/tv/Program/Season 1/Program - S02E01.mp4', 'w') as f:
        # Correct episode number, wrong season number
        f.write('S02E01')
    with pytest.raises(NamingSchemaError) as e:
        Mover('/tv/Program/Season 1', '/tv/Program/Season 2').move()
    expected_error = (
        'Season number in folder and filename differ in '
        '"/tv/Program/Season 1/Program - S02E01.mp4"'
    )
    assert expected_error == str(e.value)


def test_move_season(fs):
    os.makedirs('/tv/Program/Season 1')
    create_program_info(seasons={1: [1]})
    os.chdir('/tv/Program')
    with open('/tv/Program/Season 1/Program - S01E01.mp4', 'w') as f:
        f.write('S01E01')
    Mover('/tv/Program/Season 1', '/tv/Program/Season 2').move()
    assert not os.path.exists('/tv/Program/Season 1')
    assert os.path.exists('/tv/Program/Season 2')
    assert len(os.listdir('/tv/Program/Season 2/')) == 1
    assert os.path.exists('/tv/Program/Season 2/Program - S02E01.mp4')
    pi = ProgramInfo('/tv/Program')
    assert 1 not in pi.seasons
    assert 2 in pi.seasons
    assert len(pi.seasons[2]) == 1
    assert pi.seasons[2][0].episode.number == 1


def test_move_episode_raises_if_moving_between_seasons(fs):
    os.makedirs('/tv/Program/Season 1')
    os.makedirs('/tv/Program/Season 2')
    with open('/tv/Program/Season 1/S01E01.mp4', 'w') as f:
        f.write('S01E01')
    create_program_info(seasons={1: [1]})
    with pytest.raises(RuntimeError) as e:
        Mover(
            '/tv/Program/Season 1/Program - S01E01.mp4',
            '/tv/Program/Season 2/Program - S02E01.mp4',
        ).move()
    assert 'Moving episodes between seasons is not supported' in str(e.value)


def test_move_episode_fails_if_src_episode_not_exists_in_program_info(fs):
    os.makedirs('/tv/Program/Season 1')
    create_program_info(seasons={1: []})
    with open('/tv/Program/Season 1/S01E01.mp4', 'w') as f:
        f.write('S01E01')
    with pytest.raises(ProgramInfoError) as e:
        Mover(
            '/tv/Program/Season 1/Program - S01E01.mp4',
            '/tv/Program/Season 1/Program - S01E02.mp4',
        ).move()
    assert 'Source episode not found in program info file' in str(e.value)


def test_move_episode_fails_if_dst_episode_exists_in_program_info(fs):
    os.makedirs('/tv/Program/Season 1')
    create_program_info(seasons={1: [1, 2]})
    with open('/tv/Program/Season 1/S01E01.mp4', 'w') as f:
        f.write('S01E01')
    with pytest.raises(ProgramInfoError) as e:
        Mover(
            '/tv/Program/Season 1/Program - S01E01.mp4',
            '/tv/Program/Season 1/Program - S01E02.mp4',
        ).move()
    assert 'Destination episode found in program info file' in str(e.value)


def test_move_episode_requires_correct_naming_schema(fs):
    os.makedirs('/tv/Program/Season 1/')
    create_program_info(seasons={1: [1]})
    with open('/tv/Program/Season 1/S01E01.mp4', 'w') as f:
        f.write('incorrect name')
    with open('/tv/Program/Season 1/Program 1x1.mp4', 'w') as f:
        f.write('incorrect name')
    with open('/tv/Program/Season 1/NotProgram 1x1.mp4', 'w') as f:
        f.write('incorrect name')
    with open('/tv/Program/Season 1/Program - S01E01.mp4', 'w') as f:
        f.write('correct name')

    with pytest.raises(NamingSchemaError) as e:
        Mover(
            '/tv/Program/Season 1/S01E01.mp4',
            '/tv/Program/Season 1/Program - S01E02.mp4',
        ).move()
    assert 'Episode/season number not determined from' in str(e.value)

    with pytest.raises(NamingSchemaError) as e:
        Mover(
            '/tv/Program/Season 1/Program 1x1.mp4',
            '/tv/Program/Season 1/Program - S01E02.mp4',
        ).move()
    assert 'Episode/season number not determined from' in str(e.value)

    with pytest.raises(NamingSchemaError) as e:
        Mover(
            '/tv/Program/Season 1/NotProgram.mp4',
            '/tv/Program/Season 1/Program - S01E02.mp4',
        ).move()
    assert 'Episode/season number not determined from' in str(e.value)


def test_move_episode(fs):
    os.makedirs('/tv/Program/Season 1/')
    create_program_info(seasons={1: [1]})
    with open('/tv/Program/Season 1/Program - S01E01.mp4', 'w') as f:
        f.write('correct name')
    Mover(
        '/tv/Program/Season 1/Program - S01E01.mp4',
        '/tv/Program/Season 1/Program - S01E02.mp4',
    ).move()
    assert os.path.exists('/tv/Program/Season 1/Program - S01E02.mp4')
    assert not os.path.exists('/tv/Program/Season 1/Program - S01E01.mp4')

    pi = ProgramInfo('/tv/Program')
    assert 1 in pi.seasons
    season = pi.seasons[1]
    assert len(season) == 1
    entry = season[0]
    assert entry.episode.number == 2
