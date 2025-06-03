"""Configuration settings for the program."""

APP_NAME = "Solidity GUI"
"""The name of the app."""

APP_AUTHOR = "Imperial College London"
"""The author of the app."""

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

SOLIDITY_MAT_FILE_NAME = "mat.txt"
"""Solidity mat file name."""

SOLIDITY_LAYOUT_FILE_NAME = "layout.txt"
"""Solidity layout file name, which provides format for elements and particles."""

SOLIDITY_PELLET_FILE_NAME = "pellet.txt"
"""Solidity file name for elements and particles file."""

SOLIDITY_MATERIALS_FILE_NAME = "mat.txt"
"""Solidity materials file name."""

SOLIDITY_Y3D_TEMPLATE_FILE = "BST.Y3D.jinja"
"""Solidity Y3D template file."""

SOLIDITY_MAT_TEMPLATE_FILE = "mat.txt.jinja"
"""Solidity mat.txt template file."""

_DOCKER_IMAGE_DIGEST = (
    "9bb01c610e0e4bef14f2cbfd2bb4855c502825dc23558ad313e267ea8993b97f"
)
"""The SHA256 digest for the Docker image. Used to pull a specific version."""

DOCKER_IMAGE_ID = "9bb01c610e0e4bef14f2cbfd2bb4855c502825dc23558ad313e267ea8993b97f"
"""The content-addressable image ID for the Docker image. This is different from the
image digest above. To check what the image ID is, use the get_docker_image_id.py
script."""

DOCKER_IMAGE_ID_SHORT = DOCKER_IMAGE_ID[:12]
"""A shorter, more human-readable version of the image ID."""

SOLIDITY_DOCKER_IMAGE = (
    f"ghcr.io/imperialcollegelondon/solidity_project_dev@sha256:{_DOCKER_IMAGE_DIGEST}"
)
"""The path to the Docker image to run."""

SOLIDITY_CONTAINER_NAME = "solidity"
"""The name to use for the Docker container running Solidity."""

# ALLOWED_MAC_ADDRESSES is a JSON dictionary
ALLOWED_MAC_ADDRESSES: dict[str, str] = {}
"""The list of allowed MAC addresses for running the GUI."""
