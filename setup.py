from __future__ import annotations

import re

import setuptools  # type: ignore

with open("aiosu/__init__.py") as f:
    if search := re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
        f.read(),
        re.MULTILINE,
    ):
        version = search.group(1)

with open("README.md") as f:
    long_description = f.read()

extras_require = {
    "docs": [
        "sphinx",
    ],
    "dev": [
        "pytest",
        "pytest-asyncio",
        "pytest-mock",
    ],
}

setuptools.setup(
    name="aiosu",
    version=version,
    description="Simple and fast osu! API v1 and v2 library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NiceAesth/aiosu",
    author="Nice Aesthetics",
    author_email="nice@aesth.dev",
    license="GPLv3+",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.9",
    ],
    packages=setuptools.find_packages(),
    install_requires=["aiohttp", "aiolimiter", "orjson", "emojiflags", "pydantic"],
    extras_require=extras_require,
    python_requires=">=3.9",
    package_data={
        "aiosu": ["py.typed"],
    },
    keywords="osu! osu api",
)
