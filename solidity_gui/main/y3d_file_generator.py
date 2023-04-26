"""This module provides functionality to generate an input file for Solidity."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

from .. import config


def render_template(template_file: Template, data: dict) -> str:
    """Renders the Jinja2 template."""
    return template_file.render(data)


def write_file(rendered_template: str, output_file: str) -> None:
    """Generates the Y3D file."""
    try:
        with open(output_file, "w") as f:
            f.write(rendered_template)
    except Exception as e:
        raise Exception(f"An error occurred while writing to the output file: {e}") from e


def generate_y3d_file() -> None:
    """Generates a Solidity input file based on a Jinja2 template."""
    template_path = Path(__file__).absolute().parent.parent / "templates"
    template_file = Environment(
        loader=FileSystemLoader(str(template_path))
    ).get_template(config.SOLIDITY_Y3D_TEMPLATE_FILE)

    output_file = config.SOLIDITY_Y3D_FILE_NAME

    data = {"num_timesteps": 2000000}

    rendered_template = render_template(template_file, data)

    write_file(rendered_template, output_file)
