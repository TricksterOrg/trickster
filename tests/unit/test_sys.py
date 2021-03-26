import os

import pytest

from trickster.sys import remove_file, multi_glob, get_env


@pytest.mark.unit
class TestFileManipulation:
    def test_remove_regular_file(self, tmpdir):
        file = tmpdir.join('test.file').ensure()
        remove_file(file)
        assert not file.exists()

    def test_remove_directory(self, tmpdir):
        directory = tmpdir.mkdir('test_directory')
        remove_file(directory)
        assert not directory.exists()

    def test_glob_matches_only_selected_files(self, tmpdir):
        directory = tmpdir.mkdir('test_directory')
        file1 = directory.join('match1.file').ensure()
        file2 = directory.join('match2.file').ensure()
        file3 = directory.join('dont_match.file').ensure()

        results = list(multi_glob(f'{directory}/match1.*', f'{directory}/match2.*'))

        assert results == [
            f'{directory}/match1.file',
            f'{directory}/match2.file'
        ]

@pytest.mark.unit
class TestEnvironment:
    def test_get_env_variable(self, monkeypatch):
        monkeypatch.setenv('VARIABLE', 'VALUE')
        assert get_env('VARIABLE') == 'VALUE'

    def test_get_env_variable_not_present(self, monkeypatch):
        assert get_env('VARIABLE') is None