import shutil
import tomllib
from pathlib import Path
from typing import Final

import frontmatter
import typer
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
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
    styles_dir = Path('./styles')
    static_dir = Path('./static')

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

    try:
        template = env.get_template('index.html')
        rendered_html = template.render()

        with open(public_dir / 'index.html', 'w') as f:
            f.write(rendered_html)
    except TemplateNotFound:
        typer.secho(
            'Could not find an index.html template', fg=typer.colors.BRIGHT_RED
        )
        raise typer.Exit()

    for item in contents_dir.iterdir():
        if item.is_dir():
            section_name = item.name
            section_dir = public_dir / section_name
            section_dir.mkdir(parents=True, exist_ok=True)
            index_file = item / '_index.md'

            if index_file.exists():
                page = frontmatter.load(index_file)
                html = markdown(page.content)
                template = env.get_template(page.metadata.get('template'))
                page_dict = {**page.metadata, 'content': html}
                rendered_html = template.render(page=page_dict)

                with open(section_dir / 'index.html', 'w') as f:
                    f.write(rendered_html)

            for file in item.iterdir():
                page = frontmatter.load(file)
                html = markdown(page.content)
                template = env.get_template(page.metadata.get('template'))
                page_dict = {**page.metadata, 'content': html}
                rendered_html = template.render(page=page_dict)

                with open(section_dir / f'{file.stem}.html', 'w') as f:
                    f.write(rendered_html)

        elif item.suffix == '.md':
            page = frontmatter.load(item)
            html = markdown(page.content)
            template = env.get_template(page.metadata.get('template'))
            page_dict = {**page.metadata, 'content': html}
            rendered_html = template.render(page=page_dict)
            output_page = public_dir / f'{item.stem}.html'

            with open(output_page, 'w') as f:
                f.write(rendered_html)

    typer.secho('Site built successfully', fg=typer.colors.GREEN)
