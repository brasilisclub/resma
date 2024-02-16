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
