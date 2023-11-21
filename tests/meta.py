import pytest

from trickster import meta


class TestGetMetadata:
    def test_get_metadata_is_cached(self):
        assert meta.get_metadata() is meta.get_metadata()

    def test_get_metadata(self, tmpdir, mocker):
        meta.get_metadata.cache_clear()

        readme_file = tmpdir.join('README.md')
        readme_file.write('#Trickster')

        pyproject_file = tmpdir.join('pyproject.toml')
        pyproject_file.write('''
[tool.poetry]
name = "AppName"
description = "AppDescription"
version = "1.2.3"
authors = ["Jakub Tesarek <jakub@tesarek.me>"]
readme = 'README.md'
        ''')
        mocker.patch('trickster.meta.project_root', tmpdir)

        metadata = meta.get_metadata()
        assert metadata.name == 'AppName'
        assert metadata.description == "AppDescription"
        assert metadata.version == "1.2.3"
        assert metadata.authors == ["Jakub Tesarek <jakub@tesarek.me>"]
        assert str(metadata.readme) == str(readme_file)

    def test_get_metadata_file_not_exist(self, tmpdir, mocker):
        meta.get_metadata.cache_clear()
        mocker.patch('trickster.meta.project_root', tmpdir)

        with pytest.raises(meta.MetadataError):
            meta.get_metadata()

    def test_get_metadata_missing_key(self, tmpdir, mocker):
        meta.get_metadata.cache_clear()

        pyproject_file = tmpdir.join('pyproject.toml')
        pyproject_file.write('''
[tool.poetry]
name = "AppName"
description = "AppDescription"
version = "1.2.3"
authors = ["Jakub Tesarek <jakub@tesarek.me>"]
        ''')
        mocker.patch('trickster.meta.project_root', tmpdir)

        with pytest.raises(meta.MetadataError):
            meta.get_metadata()
