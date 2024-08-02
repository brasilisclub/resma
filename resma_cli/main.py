import locale
import shutil
from pathlib import Path
from typing import Final

import tomllib  # noqa
import typer
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from typer import Typer

from .jinja_globals import rel_path
from .process_md import process_markdown

app = Typer()

CURRENT_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()
TEMPLATES_DIR: Final[Path] = CURRENT_SCRIPT_PATH.parent / 'templates'


@app.callback()
def main():
    """Resma CLI Static Site Generator"""
    ...


@app.command()
def start(name: str):
    """Start a new project"""

    project_dir = Path(name)
    try:
        project_dir.mkdir()
    except FileExistsError as e:
        print('File already exists. Detail: ', e)
        raise typer.Abort() from e

    (project_dir / 'content').mkdir()
    (project_dir / 'templates').mkdir()
    (project_dir / 'static').mkdir()
    (project_dir / 'styles').mkdir()

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template('config.toml.jinja2')
    config = template.render(name=name)
    with open(
        project_dir / 'config.toml',
        'w',
        encoding=locale.getpreferredencoding(False),
    ) as f:
        f.write(config)

    styled_name = typer.style(name, fg=typer.colors.GREEN)
    typer.secho(f'Project {styled_name} created successfully', bold=True)


@app.command()
def build():
    """Build your site to the public folder"""
    # searching for config.toml
    config_file = Path('.') / 'config.toml'

    if not config_file.exists():
        typer.secho('Not a resma project', fg=typer.colors.RED)
        raise typer.Abort()

    with config_file.open('rb') as f:
        config_toml = tomllib.load(f)

    # config file should have resma table
    resma_table = config_toml.get('resma')

    if not resma_table:
        typer.secho(
            'config.toml should have a resma table', fg=typer.colors.RED
        )
        raise typer.Abort()

    # resma project identified, now we can build
    root_dir = Path('.')
    contents_dir = Path('./content')
    styles_dir = Path('./styles')
    static_dir = Path('./static')
    templates_dir = Path('./templates')
    public_dir = Path('public')
    public_dir.mkdir(exist_ok=True)

    should_be_on_public = [styles_dir, static_dir]

    for dir in should_be_on_public:
        shutil.copytree(
            src=dir,
            dst=public_dir / dir.name,
            dirs_exist_ok=True,
        )

    env = Environment(loader=FileSystemLoader(templates_dir))
    env.globals['rel_path'] = rel_path

    try:
        env.get_template('index.html')
    except TemplateNotFound as e:
        typer.secho(
            'Could not find an index.html template', fg=typer.colors.BRIGHT_RED
        )
        raise typer.Abort() from e

    for item in contents_dir.iterdir():
        if item.is_dir():
            section_name = item.name
            section_dir = public_dir / section_name
            section_dir.mkdir(parents=True, exist_ok=True)
            index_file = item / '_index.md'

            if index_file.exists():
                process_markdown(
                    file=index_file,
                    jinja_env=env,
                    content_dir=contents_dir,
                    public_dir=public_dir,
                    root_dir=root_dir,
                )
            for file in item.glob('*.md'):
                if file == index_file:
                    continue

                process_markdown(
                    file=file,
                    jinja_env=env,
                    content_dir=contents_dir,
                    public_dir=public_dir,
                    root_dir=root_dir,
                    section_dir=section_dir,
                )
        elif item.suffix == '.md':
            process_markdown(
                file=item,
                jinja_env=env,
                content_dir=contents_dir,
                public_dir=public_dir,
                root_dir=root_dir,
            )

    typer.secho('Site built successfully', fg=typer.colors.GREEN)
