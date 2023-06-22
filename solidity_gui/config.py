"""Configuration settings for the program."""

APP_NAME = "Solidity GUI"
"""The name of the app."""

MESH_COLOUR = (1, 1, 1, 1)  # white
"""Colour of rendered mesh components (RGBA format)."""

MESH_SELECTION_COLOUR = (1, 0, 0, 1)  # red
"""Colour of selected mesh components (RGBA format)."""

BACKGROUND_COLOUR = (0.1, 0.2, 0.4)  # a dark blue
"""Background colour of vtk display window."""

TREE_VIEW_WIDTH = 200
"""Width of Tree View on left-hand side."""

TOOLBAR_ICON_SIZE = (16, 16)
"""Size of icons in toolbar (width, height)."""

CENTRAL_LAYOUT_SPACING = 20
"""Spacing between elements in central layout."""

COMMAND_BOX_MAXIMUM_HEIGHT = 100
"""Maximum height of the command box."""

DEFAULT_ORIENTATION_VECTOR = (1, 0, 0)
"""Default camera orientation."""

DEFAULT_UP_VECTOR = (0, 1, 0)
"""Default up direction for camera."""

SOLIDITY_Y3D_FILE_NAME = "BST.Y3D"
"""Solidity Y3D file name."""

SOLIDITY_LAYOUT_FILE_NAME = "layout.txt"
"""Solidity layout file name, which provides format for elements and particles."""

SOLIDITY_PELLET_FILE_NAME = "pellet.txt"
"""Solidity file name for elements and particles file."""

SOLIDITY_MATERIALS_FILE_NAME = "mat.txt"
"""Solidity materials file name."""

SOLIDITY_Y3D_TEMPLATE_FILE = "BST.Y3D.jinja"
"""Solidity Y3D template file."""

_DOCKER_IMAGE_DIGEST = (
    "b4384d92959f5f4ff9c2bd616fefde722be5e82645ebd27971879db454ae7d21"
)
"""The SHA256 digest for the Docker image. Used to pull a specific version."""

SOLIDITY_DOCKER_IMAGE = (
    f"ghcr.io/imperialcollegelondon/solidity_project_dev@sha256:{_DOCKER_IMAGE_DIGEST}"
)
"""The name of the Docker image to use when running Solidity."""
