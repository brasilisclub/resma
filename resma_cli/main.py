from pathlib import Path
from typing import Final

from jinja2 import Environment, FileSystemLoader
from typer import Typer

app = Typer()

CURRENT_SCRIPT_PATH = Path(__file__).resolve()
TEMPLATES_DIR: Final[Path] = CURRENT_SCRIPT_PATH.parent / 'templates'


@app.command()
def start(name: str):
    """Start a new project"""

    project_dir = Path(name)
    project_dir.mkdir()
    (project_dir / 'content').mkdir()
    (project_dir / 'templates').mkdir()
    (project_dir / 'static').mkdir()
    (project_dir / 'styles').mkdir()

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template('config.toml.jinja2')
    config = template.render(name=name)
    with open(project_dir / 'config.toml', 'w') as f:
        f.write(config)

    print(f'Project {name} created successfully')


@app.callback()
def main():
    """Resma CLI Static Site Generator"""
    ...
