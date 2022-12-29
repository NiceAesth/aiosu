aiosu
=====

|Python| |pypi| |pre-commit.ci status| |rtd| |pytest| |mypy|

Simple and fast osu! API v1 and v2 library


Features
--------

- Support for API v1 and API v2
- Rate limit handling
- Utilities for osu! related calculations
- Easy to use


Installing
----------

**Python 3.9 or higher is required**

To install the library, simply run the following commands

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U aiosu

    # Windows
    py -3 -m pip install -U aiosu

To install the development version, do the following:

.. code:: sh

    $ git clone https://github.com/NiceAesth/aiosu
    $ cd aiosu
    $ python3 -m pip install -U .


API v1 Example
--------------

.. code:: py

   import aiosu
   import asyncio


   async def main():
       # async with syntax
       async with aiosu.v1.Client("osu api token") as client:
           user = await client.get_user(7782553)

       # regular syntax
       client = aiosu.v1.Client("osu api token")
       user = await client.get_user(7782553)
       client.close()


   if __name__ == "__main__":
       asyncio.run(main())


API v2 Example
--------------

.. code:: py

    import aiosu
    import asyncio
    import datetime


    async def main():
        token = aiosu.models.OAuthToken.parse_obj(json_token_from_api)

        # or

        token = aiosu.models.OAuthToken(
            access_token="access token",
            refresh_token="refresh token",
            expires_on=datetime.datetime.utcnow()
            + datetime.timedelta(days=1),  # can also be string
        )

        # async with syntax
        async with aiosu.v2.Client(
            client_secret="secret", client_id=1000, token=token
        ) as client:
            user = await client.get_me()

        # regular syntax
        client = aiosu.v2.Client(client_secret="secret", client_id=1000, token=token)
        user = await client.get_me()
        await client.close()


    if __name__ == "__main__":
        asyncio.run(main())


You can find more examples in the examples directory.


Contributing
------------

Please read the `CONTRIBUTING.rst <.github/CONTRIBUTING.rst>`__ to learn how to contribute to aiosu!


Acknowledgments
---------------

-  `discord.py <https://github.com/Rapptz/discord.py>`__
   for README formatting
-  `osu!Akatsuki <https://github.com/osuAkatsuki/performance-calculator>`__
   for performance and accuracy utils


.. |Python| image:: https://img.shields.io/pypi/pyversions/aiosu.svg
    :target: https://pypi.python.org/pypi/aiosu
    :alt: Python version info
.. |pypi| image:: https://img.shields.io/pypi/v/aiosu.svg
    :target: https://pypi.python.org/pypi/aiosu
    :alt: PyPI version info
.. |pre-commit.ci status| image:: https://results.pre-commit.ci/badge/github/NiceAesth/aiosu/master.svg
    :target: https://results.pre-commit.ci/latest/github/NiceAesth/aiosu/master
    :alt: pre-commit.ci status
.. |pytest| image:: https://github.com/NiceAesth/aiosu/actions/workflows/pytest.yml/badge.svg
    :target: https://github.com/NiceAesth/aiosu/actions/workflows/pytest.yml
    :alt: pytest Status
.. |mypy| image:: https://github.com/NiceAesth/aiosu/actions/workflows/mypy.yml/badge.svg
    :target: https://github.com/NiceAesth/aiosu/actions/workflows/mypy.yml
    :alt: mypy Status
.. |rtd| image:: https://readthedocs.org/projects/aiosu/badge/?version=latest
    :target: https://aiosu.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
