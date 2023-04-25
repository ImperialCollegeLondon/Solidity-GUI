"""Example code which just runs Solidity with the specified arguments."""
import sys
from shutil import copyfile

from . import SolidityContainer

if __name__ == "__main__":
    container = SolidityContainer()
    copyfile(sys.argv[1], container.y3d_file_path)
    copyfile(sys.argv[2], container.layout_file_path)
    copyfile(sys.argv[3], container.pellet_file_path)
    copyfile(sys.argv[4], container.materials_file_path)
    container.run()
