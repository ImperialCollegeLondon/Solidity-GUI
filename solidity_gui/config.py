"""Configuration settings for the program."""
APP_NAME = "Solidity GUI"

"""Colour of rendered mesh components (RGBA format)."""
MESH_COLOUR = (1, 1, 1, 1)  # white

"""Colour of selected mesh components (RGBA format)."""
MESH_SELECTION_COLOUR = (1, 0, 0, 1)  # red

"""Background colour of vtk display window."""
BACKGROUND_COLOUR = (0.1, 0.2, 0.4)  # a dark blue

"""Width of Tree View on left-hand side."""
TREE_VIEW_WIDTH = 200

"""Size of icons in toolbar (width, height)."""
TOOLBAR_ICON_SIZE = (16, 16)

"""Spacing between elements in central layout."""
CENTRAL_LAYOUT_SPACING = 20

"""Maximum height of the command box."""
COMMAND_BOX_MAXIMUM_HEIGHT = 100

"""Default camera orientation."""
DEFAULT_ORIENTATION_VECTOR = (1, 0, 0)

"""Default up direction for camera."""
DEFAULT_UP_VECTOR = (0, 1, 0)

"""Solidity Y3D file name."""
SOLIDITY_Y3D_FILE_NAME = "BST.Y3D"

"""Solidity Y3D template file."""
SOLIDITY_Y3D_TEMPLATE_FILE = "BST.Y3D.jinja"
