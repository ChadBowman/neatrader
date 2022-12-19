import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="neatrader",
    version="0.1.2",
    author="chad Bowman",
    author_email="chad.bowman0+github@gmail.com",
    description="Options trading experiment using NEAT",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/ChadBowman/neatrader",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "neat-python == 0.92",
        "numpy ~= 1.23.5",
        "pandas ~= 1.5.2",
        "graphviz ~= 0.20.1",
        "matplotlib ~= 3.6.2",
        "ta ~= 0.7.0",
        "nose ~= 1.3.7"
    ]
)
