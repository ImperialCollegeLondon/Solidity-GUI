"""Import machinery for loading plugins."""

import importlib
import logging
import pkgutil
import types

KNOWN_PLUGINS: list[types.ModuleType] = []

# The below iterates through any modules present in the directory at run time and
# imports them.
for _, plugin, _ in pkgutil.iter_modules(  # type: ignore[assignment]
    __path__,
    __name__ + ".",
):
    try:
        KNOWN_PLUGINS.append(importlib.import_module(plugin))
        logging.info(f"Imported plugin: {plugin}")
    except ImportError as e:
        logging.error(f"Plugin '{plugin}' failed import sequence: {e}")
    except Exception as e:
        logging.error(f"Unknown error while importing plugin '{plugin}':{e}")
