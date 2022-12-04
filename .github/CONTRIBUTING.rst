How To Contribute
=================

Thank you for considering to contribute to ``aiosu``!

This document is here to help you get started by showing you the expectations for contributions and make it more accesible to everyone.
You are still free to open unfinished PRs and ask questions though!


Support
-------

In case you'd like to ask questions, you can contact me on `Discord`_.


Code style
----------

``aiosu`` uses `black`_ formatting. It is recommended that you use the provided `pre-commit`_ hook to aid you in maintaining proper styling.

Imports that are only used for typing must be put in an `if TYPE_CHECKING` statement. They also must be the last imports in the file.


Local development environment
-----------------------------

``aiosu`` uses `poetry`_ for publishing and managing environments. You may use the provided ``dev`` group.


Documentation
-------------

``aiosu`` uses `Sphinx`_ formatting for docstrings. You should also familiarize yourself with `reStructuredText`_.


Versioning
----------

``aiosu`` uses `semantic versioning`_. Version numbers are formatted as follows: ``MAJOR.MINOR.PATCH``.


Publishing a release
--------------------

In order to publish a release, you may use the provided ``Makefile``.

.. code:: sh

    Publish without bumping version number
    $ make release

    $ make release ver=<args>

Valid arguments for release versions can be found `here <https://python-poetry.org/docs/cli/#version>`__


.. _`Discord`:  https://discord.gg/ufHV3T3UPD
.. _`pre-commit`: https://pre-commit.com/
.. _`black`: https://github.com/psf/black
.. _`poetry`: https://python-poetry.org/
.. _`Sphinx`: https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html
.. _`semantic versioning`: https://semver.org/
.. _reStructuredText: http://www.sphinx-doc.org/en/stable/rest.html
