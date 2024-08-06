import locale

import pytest
from typer.testing import CliRunner

from resma.main import app

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

    # erasing resma table from config.toml
    with open(
        'config.toml', 'w', encoding=locale.getpreferredencoding(False)
    ) as f:
        f.write('')
    result = runner.invoke(app, ['build'])

    assert result.exit_code == 1
    assert 'config.toml should have a resma table' in result.output


@pytest.mark.parametrize(
    ('args', 'expected_output', 'expected_exit_code'),
    [
        ([], 'Missing command', 2),
        (
            ['--help'],
            'Resma CLI Static Site Generator',
            0,
        ),
    ],
    ids=['default', 'help'],
)
def test_main(args, expected_output, expected_exit_code):
    result = runner.invoke(app, args)

    assert result.exit_code == expected_exit_code
    assert expected_output in result.output


def test_build_full_resma_project_ok(full_resma_project, monkeypatch):
    monkeypatch.chdir(full_resma_project)
    result = runner.invoke(app, ['build'])

    assert result.exit_code == 0
    assert 'Site built successfully' in result.output
