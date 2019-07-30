import datetime

from ruv_dl.data import Entry, EntrySet, Episode


def test_entry_from_dict():
    data = {
        'fn': 'some_fn',
        'url': 'some_url',
        'date': '2017/06/14',
        'etag': 'some_etag',
        'episode': {'id': 'some_episode'},
    }
    e = Entry.from_dict(data)
    assert e.fn == data['fn']
    assert e.url == data['url']
    assert e.date == datetime.datetime(2017, 6, 14)
    assert e.etag == data['etag']
    assert e.episode.data == data['episode']

    del data['episode']
    e = Entry.from_dict(data)
    assert e.episode.data == {}


def test_entry_to_dict():
    e = Entry(
        'some_fn', 'some_url', datetime.datetime(2017, 6, 14),
        'some_etag', {'id': 'some_episode'}
    )
    assert e.to_dict() == {
        'fn': 'some_fn',
        'url': 'some_url',
        'date': '2017/06/14',
        'etag': 'some_etag',
        'episode': {'id': 'some_episode'},
    }


def test_entry_equality():
    assert Entry('fdsa', 'fdsa', None, 'etag') == Entry(
        'asdf', 'asdf', datetime.datetime.min, 'etag'
    )
    assert Entry('fdsa', 'fdsa', None, 'etag') == Entry(
        'fdsa', 'fdsa', None, 'etag'
    )
    assert Entry('fdsa', 'fdsa', None, 'etag') != Entry(
        'fdsa', 'fdsa', None, 'not-same-etag'
    )


def test_choose_best_item():
    s = EntrySet()
    episode_real = {
        'id': 'some_id_from_ruv_api',
        'number': 1,
    }
    episode_generated = {
        'number': 2,
    }
    item1 = Entry('fn1', 'url1', datetime.datetime.min, 'etag1', None)
    item2 = Entry(
        'fn2', 'url2', datetime.datetime.min, 'etag2', episode_real
    )
    assert s._choose_best_item(item1, item2).episode.to_dict() == episode_real
    assert s._choose_best_item(item2, item1).episode.to_dict() == episode_real

    item1.episode = Episode(episode_generated)
    assert s._choose_best_item(item1, item2).episode.to_dict() == episode_real
    assert s._choose_best_item(item2, item1).episode.to_dict() == episode_real

    item2.episode = None
    assert s._choose_best_item(
        item1, item2).episode.to_dict() == episode_generated
    assert s._choose_best_item(
        item2, item1).episode.to_dict() == episode_generated
