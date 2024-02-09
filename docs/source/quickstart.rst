:orphan:

.. _quickstart:

.. currentmodule:: aiosu

Quickstart
============


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
       await client.aclose()


   if __name__ == "__main__":
       asyncio.run(main())


API v2 Example
--------------

.. code:: py

    import aiosu
    import asyncio
    import datetime


    async def main():
        token = aiosu.models.OAuthToken.model_validate(json_token_from_api)

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
        await client.aclose()


    if __name__ == "__main__":
        asyncio.run(main())

More examples can be found in the `repository <https://github.com/NiceAesth/aiosu/tree/master/examples>`__
