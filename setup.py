#!/usr/bin/env python

"""
 * Copyright(c) 2022 ZettaScale Technology and others
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License v. 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0, or the Eclipse Distribution License
 * v. 1.0 which is available at
 * http://www.eclipse.org/org/documents/edl-v10.php.
 *
 * SPDX-License-Identifier: EPL-2.0 OR BSD-3-Clause
"""

import os
import platform
from pathlib import Path
from setuptools import setup, Extension, find_packages


class FoundCyclone(Exception):
    def __init__(self, location) -> None:
        self.location = location
        super().__init__()


def search_cyclone_pathlike(pathlike, upone=False):
    for path in pathlike.split(os.pathsep):
        if path != "":
            try:
                path = Path(path).resolve()
                if upone:
                    path = (path / '..').resolve()
                if (path / 'lib' / 'cmake' / 'CycloneDDS' / 'CycloneDDSConfig.cmake').exists():
                    return path
            except:
                pass


def find_cyclonedds():
    if "CYCLONEDDS_HOME" in os.environ:
        return Path(os.environ["CYCLONEDDS_HOME"])
    if "CycloneDDS_ROOT" in os.environ:
        return Path(os.environ["CMAKE_CycloneDDS_ROOT"])
    if "CycloneDDS_ROOT" in os.environ:
        return Path(os.environ["CycloneDDS_ROOT"])
    if "CMAKE_PREFIX_PATH" in os.environ:
        dir = search_cyclone_pathlike(os.environ["CMAKE_PREFIX_PATH"])
        if dir:
            return dir
    if "CMAKE_LIBRARY_PATH" in os.environ:
        dir = search_cyclone_pathlike(os.environ["CMAKE_LIBRARY_PATH"])
        if dir:
            return dir
    if platform.system() != "Windows" and "LIBRARY_PATH" in os.environ:
        dir = search_cyclone_pathlike(os.environ["LIBRARY_PATH"], upone=True)
        if dir:
            return dir
    if platform.system() != "Windows" and "LD_LIBRARY_PATH" in os.environ:
        dir = search_cyclone_pathlike(os.environ["LD_LIBRARY_PATH"], upone=True)
        if dir:
            return dir
    if platform.system() == "Windows" and "PATH" in os.environ:
        dir = search_cyclone_pathlike(os.environ["PATH"], upone=True)
        if dir:
            return dir


this_directory = Path(__file__).resolve().parent
with open(this_directory / 'README.md', encoding='utf-8') as f:
    long_description = f.read()


cyclone = find_cyclonedds()

if not cyclone:
    print("Could not locate cyclonedds. Try to set CYCLONEDDS_HOME or CMAKE_PREFIX_PATH")
    import sys
    sys.exit(1)


cyclone_library = None
for file in cyclone.rglob("*ddsc*"):
    if file.suffix in [".dll", ".so", ".dynlib"]:
        cyclone_library = file
        break

with open(this_directory / 'cyclonedds' / '__library__.py', "w", encoding='utf-8') as f:
    f.write(f"library_path = '{cyclone_library}'")


console_scripts = [
    "ddsls=cyclonedds.tools.ddsls:command",
    "pubsub=cyclonedds.tools.pubsub:command"
]
cmake_args = []


if "CIBUILDWHEEL" in os.environ:
    # We are building wheels! This means we should be including the idl compiler in the
    # resulting package. To do this we need to include the idlc executable and libidl,
    # this is done by cmake. We will add an idlc entrypoint that will make sure the load paths
    # of idlc are correct.
    console_scripts.append("idlc=cyclonedds.tools.wheel_idlc:command")


setup(
    name='cyclonedds',
    version='0.9.0',
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent"
    ],
    packages=find_packages(".", exclude=("tests", "tests.*", "docs.*")),
    package_data={
        "cyclonedds": ["*.so", "*.dylib", "*.dll", "idlc*", "*py.typed"],
        "cyclonedds.idl": ["py.typed"]
    },
    ext_modules=[
        Extension('cyclonedds._clayer', [
                'clayer/cdrkeyvm.c',
                'clayer/pysertype.c',
                'clayer/typeser.c'
            ],
            include_dirs=[
                f"{cyclone}/include",
                str(this_directory / "clayer")
            ],
            libraries=['cycloneddsidl', 'ddsc'],
            library_dirs=[
                f"{cyclone}/lib",
                f"{cyclone}/lib64",
                f"{cyclone}/bin"
            ]
        )
    ],
    entry_points={
        "console_scripts": console_scripts,
    },
    python_requires='>=3.7',
    install_requires=[
        "typing-inspect>=0.6;python_version<'3.7'",
        "typing-extensions>=3.7;python_version<'3.9'"
    ],
    extras_require={
        "dev": [
            "pytest>=6.2",
            "pytest-cov",
            "pytest-mock",
            "flake8",
            "flake8-bugbear",
            "twine"
        ],
        "docs": [
            "Sphinx>=4.0.0",
            "sphinx-rtd-theme>=0.5.2"
        ]
    },
    zip_safe=False
)
