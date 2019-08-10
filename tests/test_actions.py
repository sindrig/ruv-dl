import os
from click.testing import CliRunner

from ruv_dl import mv

runner = CliRunner()


def test_mv(fs, mocker):
    os.makedirs('/a/b/c')
    os.chdir('/a/b')
    mover_patch = mocker.patch('ruv_dl.Mover')
    runner.invoke(mv, ['c', 'd'])
    mover_patch.assert_called_once_with('/a/b/c', '/a/b/d')
    mover_patch().move.assert_called_once_with()
