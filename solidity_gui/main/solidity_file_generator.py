"""This module provides functionality to generate an input file for Solidity."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

from .. import config

env = Environment(
    loader=FileSystemLoader(str(Path(__file__).absolute().parent.parent / "templates"))
)


def write_file(file_content: str, output_file: Path | str) -> None:
    """Write the contents of file_content to file."""
    try:
        with open(output_file, "w") as f:
            f.write(file_content)
    except IOError as e:
        raise Exception(
            f"An error occurred while writing to the output file: {e}"
        ) from e


def create_y3d_template() -> str:
    """Creates a Solidity input template using Jinja2."""
    template = env.get_template(config.SOLIDITY_Y3D_TEMPLATE_FILE)

    data = {"num_timesteps": 2000000}

    return template.render(data)


def generate_y3d_file() -> None:
    """Generates a Solidity input file based on a Jinja2 template."""
    file_content = create_y3d_template()
    write_file(file_content, config.SOLIDITY_Y3D_FILE_NAME)
