import locale
from pathlib import Path

import frontmatter
from jinja2 import Environment, TemplateNotFound
from markdown import markdown  # type: ignore

from resma_cli.images import copy_images_and_update_path
from resma_cli.utils import calculate_depth


def process_markdown(
    file: Path,
    jinja_env: Environment,
    content_dir: Path,
    public_dir: Path,
    root_dir: Path,
    section_dir: Path | None = None,
):
    page = frontmatter.load(file)
    if (
        not page.metadata
        or not page.metadata.get('template')
        or not page.metadata.get('title')
    ):
        raise ValueError(f'Frontmatter of {file} malformed')
    corrected_content = copy_images_and_update_path(
        content_dir, public_dir / 'static', file, root_dir, page.content
    )

    html = markdown(corrected_content)
    try:
        template = jinja_env.get_template(page.metadata.get('template'))
    except TemplateNotFound:
        raise TemplateNotFound(
            f"Template {page.metadata.get('template')} not found"
        )

    page_dict = {
        **page.metadata,
        'content': html,
        'depth': calculate_depth(file, root_dir),
    }

    rendered_html = template.render(page=page_dict)
    html_file_name = (
        'index.html' if file.stem == '_index' else f'{file.stem}.html'
    )
    output_dir = section_dir or public_dir

    with open(
        output_dir / html_file_name,
        'w',
        encoding=locale.getpreferredencoding(False),
    ) as f:
        f.write(rendered_html)
