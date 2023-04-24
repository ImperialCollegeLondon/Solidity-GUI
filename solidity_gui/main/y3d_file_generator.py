"""This module provides functionality to generate an input file for Solidity."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .. import config


class Y3DFileGenerator:
    """A class that generates a Solidity input file based on a Jinja2 template."""

    def __init__(self) -> None:
        """Initializes a new instance of the Y3DFileGenerator class."""
        template_path = Path(__file__).absolute().parent
        #template_path = Path("./solidity_gui/main/")
        self.template_file = Environment(
            loader=FileSystemLoader(str(template_path))
        ).get_template(config.SOLIDITY_Y3D_TEMPLATE_FILE)

        self.output_file = config.SOLIDITY_Y3D_FILE_NAME

        self.data = {"num_timesteps": 2000000}

    def generate_y3d_file(self) -> None:
        """Generates an input file by rendering the Jinja2 template."""
        rendered_template = self.template_file.render(self.data)
        try:
            with open(self.output_file, "w") as f:
                f.write(rendered_template)
        except Exception as e:
            print(f"An error occurred while writing to the output file: {e}")
