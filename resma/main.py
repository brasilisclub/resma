import http.server
import locale
import os
import shutil
import socketserver
import tomllib
from pathlib import Path
from typing import Final

import typer
from jinja2 import Environment, FileSystemLoader
from typer import Typer

from .jinja_globals import rel_path
from .process_md import process_markdown

app = Typer()

CURRENT_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()
TEMPLATES_DIR: Final[Path] = CURRENT_SCRIPT_PATH.parent / 'templates'


def validate_resma_project():
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
    validate_resma_project()
    root_path = Path('.')

    directories = {
        'root': root_path,
        'contents': root_path / 'content',
        'styles': root_path / 'styles',
        'static': root_path / 'static',
        'templates': root_path / 'templates',
        'public': Path('public'),
    }

    directories['public'].mkdir(exist_ok=True)

    # content and templates must exist and not be empty
    content_is_empty = not directories['contents'].exists() or not any(
        directories['contents'].iterdir()
    )
    template_is_empty = not directories['templates'].exists() or not any(
        directories['templates'].iterdir()
    )
    if content_is_empty or template_is_empty:
        typer.secho(
            'Content and Templates directories cannot be empty',
            fg=typer.colors.RED,
        )
        raise typer.Abort()

    for dir in [
        directories['styles'],
        directories['static'],
    ]:  # should be on public
        shutil.copytree(
            src=dir,
            dst=directories['public'] / dir.name,
            dirs_exist_ok=True,
        )

    env = Environment(loader=FileSystemLoader(directories['templates']))
    env.globals['rel_path'] = rel_path
    try:
        for item in directories['contents'].iterdir():
            if item.is_dir():
                index_file = item / '_index.md'
                section_dir = directories['public'] / item.name
                section_dir.mkdir(parents=True, exist_ok=True)
                section_pages = []

                for file in item.glob('*.md'):
                    if file != index_file:
                        page_context = process_markdown(
                            file=file,
                            jinja_env=env,
                            content_dir=directories['contents'],
                            public_dir=directories['public'],
                            root_dir=directories['root'],
                            section_dir=section_dir,
                        )
                        section_pages.append(page_context)

                    elif index_file.exists():
                        process_markdown(
                            file=index_file,
                            jinja_env=env,
                            content_dir=directories['contents'],
                            public_dir=directories['public'],
                            root_dir=directories['root'],
                            section_dir=section_dir,
                            section_pages=section_pages,
                        )

            elif item.suffix == '.md':
                process_markdown(
                    file=item,
                    jinja_env=env,
                    content_dir=directories['contents'],
                    public_dir=directories['public'],
                    root_dir=directories['root'],
                )

        typer.secho('Site built successfully', fg=typer.colors.GREEN)

    except Exception as e:
        typer.secho(f'Error: {e}', fg=typer.colors.RED)
        raise typer.Abort() from e


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if (
            'static' in self.path
            or 'styles' in self.path
            or 'favicon' in self.path
        ):
            return super().do_GET()

        if not self.path.endswith('/'):
            self.path += '/'
        if  self.path.startswith('/'):
            self.path = self.path[1:]
        index_file_path = os.path.join(self.path, 'index.html')
        if os.path.isdir(self.path) and os.path.exists(index_file_path):
            self.path += 'index.html'
        else:
            self.path = self.path[:-1] + '.html'
        print(self.path)
        return super().do_GET()


@app.command()
def serve(port: int = 8080):
    """Run a http server from public folder"""
    PORT = port
    Handler = CustomHTTPRequestHandler

    os.chdir('public')

    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        typer.secho(
            f'Serving at http://127.0.0.1:{PORT}', fg=typer.colors.GREEN
        )
        httpd.serve_forever()
