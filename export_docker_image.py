#!/usr/bin/env python
"""A tool for exporting and compressing the Solidity Docker image."""

import gzip
import os
import shutil
from pathlib import Path
from typing import cast

from python_on_whales import Image, docker

from solidity_gui.config import DOCKER_IMAGE_FILE_HASH_SHORT, SOLIDITY_DOCKER_IMAGE

if __name__ == "__main__":
    # Download image
    image = cast(Image, docker.pull(SOLIDITY_DOCKER_IMAGE))

    output_path = (
        Path(__file__).parent / f"solidity_image_{DOCKER_IMAGE_FILE_HASH_SHORT}.tar"
    )

    print(f"Exporting {SOLIDITY_DOCKER_IMAGE}...")
    docker.save(SOLIDITY_DOCKER_IMAGE, output_path)
    print(f"Successfully exported to {output_path}")

    print("Compressing with gzip...")
    with output_path.open("rb") as f_in:
        with gzip.open(str(output_path) + ".gz", "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    print("Done")

    print("Deleting original file...")
    os.remove(output_path)
