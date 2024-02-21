import tomllib
from pathlib import Path
from typing import Final

import typer
from jinja2 import Environment, FileSystemLoader
from markdown import markdown  # type: ignore
from typer import Typer

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
        print('File already exists. Detail: ', str(e))
        raise typer.Abort()

    (project_dir / 'content').mkdir()
    (project_dir / 'templates').mkdir()
    (project_dir / 'static').mkdir()
    (project_dir / 'styles').mkdir()

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template('config.toml.jinja2')
    config = template.render(name=name)
    with open(project_dir / 'config.toml', 'w') as f:
        f.write(config)

    styled_name = typer.style(name, fg=typer.colors.GREEN)
    typer.secho(f'Project {styled_name} created successfully', bold=True)


@app.command()
def build():
    """Build your site to the public folder"""
    # searching for config.toml

    config_file = Path('.') / 'config.toml'
    config_file_exists = config_file.exists()

    if not config_file_exists:
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

    contents_dir = Path('./content')
    templates_dir = Path('./templates')
    print([i for i in contents_dir.glob('*.md')])

    public_dir = Path('public')
    public_dir.mkdir(exist_ok=True)

    env = Environment(loader=FileSystemLoader(templates_dir))

    for md_file in contents_dir.glob('*.md'):
        with open(md_file, 'r') as f:
            md_content = f.read()
            print(md_content)

        html_content = markdown(md_content, extensions=['fenced_code'])
        print(html_content)
        template = env.get_template('index.html')
        rendered_html = template.render(content=html_content)
        print(rendered_html)

        output_path = public_dir / 'index.html'
        with open(output_path, 'w') as f:
            f.write(rendered_html)

    typer.secho('Site built successfully', fg=typer.colors.GREEN)
