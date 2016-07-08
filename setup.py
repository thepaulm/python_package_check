#!/usr/bin/env python

from setuptools import setup

version = '1.0.3'

setup(
    name="python_package_check",
    version=version,
    url="https://github.com/thepaulm/python_package_check",
    download_url="https://github.com/thepaulm/python_package_check",
    author="Paul Mikesell",
    author_email="pmikesell@gmail.com",
    zip_safe=False,
    install_requires=['setuptools'],
    scripts=['python_package_check.py'],
)
