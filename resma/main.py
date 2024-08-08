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
    contents_dir = root_dir / 'content'
    styles_dir = root_dir / 'styles'
    static_dir = root_dir / 'static'
    templates_dir = root_dir / 'templates'
    public_dir = Path('public')
    public_dir.mkdir(exist_ok=True)

    # content and templates must exist and not be empty
    content_is_empty = not contents_dir.exists() or not any(
        contents_dir.iterdir()
    )
    template_is_empty = not templates_dir.exists() or not any(
        templates_dir.iterdir()
    )
    if content_is_empty or template_is_empty:
        typer.secho(
            'Content and Templates directories cannot be empty',
            fg=typer.colors.RED,
        )
        raise typer.Abort()

    for dir in [styles_dir, static_dir]:  # should be on public
        shutil.copytree(
            src=dir,
            dst=public_dir / dir.name,
            dirs_exist_ok=True,
        )

    env = Environment(loader=FileSystemLoader(templates_dir))
    env.globals['rel_path'] = rel_path
    try:
        for item in contents_dir.iterdir():
            if item.is_dir():
                index_file = item / '_index.md'
                section_dir = public_dir / item.name
                section_dir.mkdir(parents=True, exist_ok=True)
                section_pages = []
                
                for file in item.glob('*.md'):
                    if file != index_file:
                        page_dict = process_markdown(
                            file=file,
                            jinja_env=env,
                            content_dir=contents_dir,
                            public_dir=public_dir,
                            root_dir=root_dir,
                            section_dir=section_dir,
                        )
                        section_pages.append(page_dict)

                    elif index_file.exists():
                        process_markdown(
                            file=index_file,
                            jinja_env=env,
                            content_dir=contents_dir,
                            public_dir=public_dir,
                            root_dir=root_dir,
                            section_dir=section_dir,
                            section_pages=section_pages
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

    except Exception as e:
        typer.secho(f'Error: {e}', fg=typer.colors.RED)
        raise typer.Abort() from e


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if 'static' in self.path or 'styles' in self.path:
            return super().do_GET()

        if self.path.endswith('/'):
            directory_path = self.path[1:]  # Remove leading '/'
            index_file_path = os.path.join(directory_path, 'index.html')
            if os.path.isdir(directory_path) and os.path.exists(
                index_file_path
            ):
                self.path += 'index.html'
            elif self.path != '/':
                self.path = self.path[:-1] + '.html'
            else:
                return super().do_GET()
        elif not os.path.isfile(self.path[1:]):
            self.path += '.html'
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
