"""Import machinery for loading plugins."""

import importlib
import logging
import pkgutil

# The below iterates through any modules present in the directory at run time and
# imports them.
for _, plugin, _ in pkgutil.iter_modules(  # type: ignore[assignment]
    __path__,
    __name__ + ".",
):
    importlib.import_module(plugin)
    logging.info(f"Imported plugin: {plugin}")
