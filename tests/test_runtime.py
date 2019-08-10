import pytest

from ruv_dl.runtime import settings


def test_cannot_set_unless_context_manager():
    with pytest.raises(RuntimeError):
        settings.dryrun = True
    assert settings.dryrun is False


def test_sets_dryrun_using_context_manager():
    with settings:
        settings.dryrun = True
    assert settings.dryrun is True
    # Reset again
    with settings:
        settings.dryrun = False
    assert settings.dryrun is False


def test_must_use_same_type_when_setting_new_value():
    with settings:
        with pytest.raises(TypeError):
            settings.dryrun = 'not a boolean'
    assert settings.dryrun is False


def test_cannot_set_unknown_setting():
    with settings:
        with pytest.raises(AttributeError):
            settings.not_a_known_key = 'something'
