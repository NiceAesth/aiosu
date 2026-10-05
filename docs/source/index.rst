.. aiosu documentation master file, created by
   sphinx-quickstart on Sat Dec  3 18:08:00 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to aiosu
================

aiosu is an easy-to-use asynchronous wrapper for the osu! API

**Features:**

- Support for modern async syntax (async with)
- Support for API v1 and API v2
- Rate limit handling
- Utilities for osu! related calculations
- Easy to use

Getting started
---------------

If you are new to this library, you should familiarize yourself with the following pages:

- **First steps:** :doc:`quickstart`
- **Examples:** Examples can be found in the `repository <https://github.com/NiceAesth/aiosu/tree/master/examples>`__

Getting help
------------

If you need assistance, you should look here:

- Try the :ref:`index <genindex>` or :ref:`searching <search>`
- Contact me on `Discord <https://discord.gg/ufHV3T3UPD>`_
- Report bugs in the `issue tracker <https://github.com/NiceAesth/aiosu/issues>`_

Breaking changes
----------------

**v3.0.0:** The following changes have occured:

- The library now requires *Python 3.12 or higher*
- The license has been changed from *GPLv3+* to *AGPLv3+*
- The `LazerScore`, `LazerScoreStatistics` and `LazerMod` classes have been removed
- The `Mod` class is no longer an enum. Named constants such as `Mod.Hidden` are still available as `Mod` objects
- The bitwise operators of `Mod` and `Mods` now return `Mods` instead of integers. Use `int()` to get the bitmask. Mods without legacy flags cannot be converted to integers
- Mods are now serialized as lists of objects instead of strings. Legacy scores serialize mods as lists of acronyms
- The `Beatmap` and `Beatmapset` classes have been split into regular and extended models. API v2 beatmap and beatmapset detail methods now return `BeatmapExtended` and `BeatmapsetExtended`
- API v1 methods now return `LegacyUser`, `LegacyBeatmapset` and `LegacyBeatmap` instead of `User`, `Beatmapset` and `Beatmap`
- The `get_users()` method and embedded users now use `UserCompact` instead of `User`. Full profile fields are only available on `User`
- Fields previously marked as optional on user and beatmap models are now required where returned by the API
- Changed `UserGroup.description` from a string to `HTMLBody`, and `CurrentUserAttributes.nomination_modes` from a list to a dictionary
- The `SeasonUserStats` fields `user_id`, `season_id`, `division_id` and `playcount` have been replaced with `season`, `division` and `rank`
- The `ScoreStatistics` fields now use hit result names. The old `count_` names are still available as properties. If you are creating the class directly, pass in `mode` to the constructor to get the correct hit result names
- Performance calculators have been updated to use the new `BeatmapDifficultyAttributes` fields. (2026-10-06)

**v2.2.0:** The `close()` methods of the clients are now named `aclose()` as per naming conventions for asynchronous methods. The old method is still available with a deprecation warning, but will be removed on 2024-03-01.

**v2.0.3:** The replay model has been moved to `models/files/replay.py` and the `Replay` class has been renamed to `ReplayFile`.

**v2.0.0:** The library now uses *Pydantic v2*. This means that the following changes have occured:

- The *dict* method has been renamed to *model_dump*
- The *json* method has been renamed to *model_dump_json*
- The *parse_obj* method has been renamed to *model_validate*
- The *parse_raw* method has been renamed to *model_validate_json*
- The *parse_file* method has been renamed to *model_validate_file*
- Renamed *Beatmapset.nomination_summary* to *Beatmapset.nominations*

Note: The old methods are still available with a deprecation warning, but will be removed in Pydantic v3.

Utilities
---------

aiosu has utilities for various osu! related calculations.

.. toctree::
   :maxdepth: 1

   utils/index.rst

Clients
-------

Documentation for the API clients can be found below.

.. toctree::
   :maxdepth: 1
   :glob:

   clients/*/*

Models
-------

Documentation for `aiosu` types can be found below.

.. toctree::
   :maxdepth: 1

   models/index.rst

Library Classes
---------------

Documentation for `aiosu` classes can be found below.

.. toctree::
   :maxdepth: 1

   library/index.rst
