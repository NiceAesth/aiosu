from __future__ import annotations

from datetime import date
from importlib import metadata

__title__ = "aiosu"
__author__ = "Nice Aesthetics"
__license__ = "GPLv3+"
__copyright__ = f"Copyright {date.today().year} Nice Aesthetics"

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    import toml

    __version__ = toml.load("pyproject.toml")["tool"]["poetry"]["version"] + "dev"

from . import classes, v1, v2, utils
