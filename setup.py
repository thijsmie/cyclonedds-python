#!/usr/bin/env python
"""
 * Copyright(c) 2021 ADLINK Technology Limited and others
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License v. 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0, or the Eclipse Distribution License
 * v. 1.0 which is available at
 * http://www.eclipse.org/org/documents/edl-v10.php.
 *
 * SPDX-License-Identifier: EPL-2.0 OR BSD-3-Clause
"""

from os import path
from skbuild import setup
from setuptools import find_packages

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='cyclonedds',
    version='0.8.0',
    description='Eclipse Cyclone DDS Python binding',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Eclipse Cyclone DDS Committers',
    maintainer='Thijs Miedema',
    maintainer_email='thijs.miedema@adlinktech.com',
    url="https://cyclonedds.io",
    project_urls={
        "Documentation": "https://cyclonedds.io/docs",
        "Source Code": "https://github.com/eclipse-cyclonedds/cyclonedds-python",
        "Bug Tracker": "https://github.com/eclipse-cyclonedds/cyclonedds-python/issues"
    },
    license="EPL-2.0, BSD-3-Clause",
    platforms=["Windows", "Linux", "Mac OS-X", "Unix"],
    keywords=[
        "eclipse", "cyclone", "dds", "pub", "sub",
        "pubsub", "iot", "cyclonedds", "cdr", "omg",
        "idl", "middleware", "ros"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Eclipse Public License 2.0 (EPL-2.0)",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent"
    ],
    packages=find_packages(".", include=("cyclonedds*")),
    entry_points={
        "console_scripts": [
            "ddsls=cyclonedds.tools.ddsls:command",
            "pubsub=cyclonedds.tools.pubsub:command"
        ],
    },
    python_requires='>=3.6',
    install_requires=[
        "dataclasses>=0.8;python_version<'3.7'",
        "typing-inspect>=0.6;python_version<'3.7'",
        "typing-extensions>=3.7;python_version<'3.9'"
    ],
    extras_require={
        "dev": [
            "pytest>=6.2",
            "pytest-cov",
            "pytest-mock",
            "pytest-virtualenv",
            "flake8",
            "flake8-bugbear",
            "flake8-docstrings",
            "twine"
        ],
        "docs": [
            "Sphinx>=4.0.0",
            "sphinx-rtd-theme>=0.5.2"
        ]
    },
    zip_safe=False
)
