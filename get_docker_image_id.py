#!/usr/bin/env python
"""A script to get the image ID for the Solidity Docker image used by Solidity-GUI."""
from typing import cast

from python_on_whales import Image, docker

from solidity_gui.config import SOLIDITY_DOCKER_IMAGE

if __name__ == "__main__":
    # Download image
    image = cast(Image, docker.pull(SOLIDITY_DOCKER_IMAGE))
    print(f'Docker image ID: {image.id.removeprefix("sha256:")}')
