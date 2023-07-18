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

**v2.0.0:** The library now uses *Pydantic v2*. This means that the following changes have occured:

- The *dict* method has been renamed to *model_dump*
- The *json* method has been renamed to *model_dump_json*
- The *parse_obj* method has been renamed to *model_validate*
- The *parse_raw* method has been renamed to *model_validate_json*
- The *parse_file* method has been renamed to *model_validate_file*

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
