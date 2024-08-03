import locale
from pathlib import Path

from typer.testing import CliRunner

from resma_cli.main import app

runner = CliRunner()


def test_start(temp_dir, monkeypatch):
    monkeypatch.chdir(temp_dir)
    result = runner.invoke(app, ['start', 'project'])

    assert result.exit_code == 0


def test_start_project_already_exists(temp_dir, monkeypatch):
    monkeypatch.chdir(temp_dir)

    runner.invoke(app, ['start', 'project'])
    result = runner.invoke(app, ['start', 'project'])

    assert result.exit_code == 1
    assert 'File already exists' in result.output


def test_build_resma_project_not_found(temp_dir, monkeypatch):
    monkeypatch.chdir(temp_dir)

    result = runner.invoke(app, ['build'])

    assert result.exit_code == 1
    assert 'Not a resma project' in result.output


def test_build_empty_project(temp_dir, monkeypatch):
    monkeypatch.chdir(temp_dir)

    runner.invoke(app, ['start', 'project'])

    monkeypatch.chdir('project')
    result = runner.invoke(app, ['build'])

    assert result.exit_code == 1
    assert 'Content and Templates directories cannot be empty' in result.output


def test_build_resma_table_not_found_in_config_toml(temp_dir, monkeypatch):
    monkeypatch.chdir(temp_dir)
    runner.invoke(app, ['start', 'project'])

    monkeypatch.chdir('project')
    (Path('.') / 'templates' / 'index.html').touch()

    # erasing resma table from config.toml
    with open(
        'config.toml', 'w', encoding=locale.getpreferredencoding(False)
    ) as f:
        f.write('')
    result = runner.invoke(app, ['build'])

    assert result.exit_code == 1
    assert 'config.toml should have a resma table' in result.output
