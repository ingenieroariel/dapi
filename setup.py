
from setuptools import setup

setup(
    name = "dapi",
    version = "0.1pre",
    description = "An out-of-box RESTful API for Django projects",
    url = "http://github.com/ingenieroariel/dapi",
    packages = [
        "dapi",
    ],
    setup_requires = [
        "setuptools_git"
    ],
)
