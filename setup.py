from distutils.core import setup
from setuptools import find_packages
from wtc.__init__ import __version__

with open("README.md", "r", encoding="utf8") as readme:
    long_description = readme.read()

setup(
    name = "wtc",
    version = __version__,
    description = "Compress osu replay lzma bytestrings",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    keywords = ["osu!, compression, lzma, python, replay, osr"],
    author = "Chris Miuchiz",
    author_email = "chrismiuchiz@gmail.com",
    url = "https://github.com/circleguard/wtc-lzma-compressor",
    download_url = "https://github.com/circleguard/wtc-lzma-compressor/tarball/v" + __version__,
    packages = find_packages()
)
