import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()

setuptools.setup(
    name="wtc",
    version="1.0.0",
    author="Chris Miuchiz",
    author_email="chrismiuchiz@gmail.com",
    description="Compress osu replay lzma bytestrings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/osu-anticheat/wtc-lzma-compressor",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
