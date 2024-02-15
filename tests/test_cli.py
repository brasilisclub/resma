from typer.testing import CliRunner

from resma_cli.main import app

runner = CliRunner()


def test_start(temp_dir, monkeypatch):
    monkeypatch.chdir(temp_dir)
    result = runner.invoke(app, ['start', 'project'])

    assert result.exit_code == 0
