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

import os
import inspect
import platform
import ctypes as ct
from . import dds_c_t
from functools import wraps
from dataclasses import dataclass
from typing import Optional, TypeVar, Type, Protocol


def load_cyclonedds() -> Optional[ct.CDLL]:
    """
        Internal method to load the Cyclone Dynamic Library.
        Handles platform specific naming/configuration.
    """
    load_method = ""
    load_path = []

    if 'CDDS_NO_IMPORT_LIBS' in os.environ:
        return None

    if 'ddsc' in os.environ:
        # library was directly specified in environment variables
        load_method = 'env'
        load_path = [os.environ['ddsc']]
    elif "CYCLONEDDS_HOME" in os.environ and platform.system() == "Linux":
        load_method = 'home'
        load_path = [os.path.join(os.environ["CYCLONEDDS_HOME"], "lib", "libddsc.so")]
    elif "CYCLONEDDS_HOME" in os.environ and platform.system() == "Darwin":
        load_method = 'home'
        load_path = [os.path.join(os.environ["CYCLONEDDS_HOME"], "lib", "libddsc.dylib")]
    elif "CYCLONEDDS_HOME" in os.environ and platform.system() == "Windows":
        load_method = 'home'
        load_path = [os.path.join(os.environ["CYCLONEDDS_HOME"], "bin", "ddsc.dll")]
    elif platform.system() == "Linux":
        load_method = "guess"
        load_path = [os.path.join(p, "libddsc.so") for p in [
            "", "/usr/lib/", "/usr/local/lib/", "/usr/lib64/", "/lib/", "/lib64/"]
        ]
    elif platform.system() == "Darwin":
        load_method = "guess"
        load_path = [os.path.join(p, "libddsc.dylib") for p in [
            "", "/usr/lib/", "/usr/local/lib/", "/usr/lib64/", "/lib/", "/lib64/"]
        ]
    else:
        load_method = "guess"
        load_path = ["libddsc.so", "ddsc.dll", "libddsc.dylib"]

    lib = None
    for path in load_path:
        try:
            lib = ct.CDLL(path)
        except OSError:
            continue
        if lib:
            break

    if not lib:
        raise Exception(f"Failed to load CycloneDDS with method {load_method} from path(s): {', '.join(load_path)}.")

    return lib


def c_call(cname):
    """
        Decorator. Convert a function into call into the class associated dll.
    """

    class DllCall:
        def __init__(self, function):
            self.function = function

        # This gets called when the class is finalized
        def __set_name__(self, cls, name):
            if 'CDDS_NO_IMPORT_LIBS' in os.environ:
                return

            s = inspect.signature(self.function)

            # Set c function types based on python type annotations
            cfunc = getattr(cls._dll_handle, cname)

            # Note: in python 3.10 we get NoneType for voids instead of None
            # This confuses ctypes a lot, so we explicitly test for it
            # We also add the ignore for the error that flake8 generates
            cfunc.restype = s.return_annotation if s.return_annotation != type(None) else None  # noqa: E721

            # Note: ignoring the 'self' argument
            cfunc.argtypes = [p.annotation for i, p in enumerate(s.parameters.values()) if i > 0]

            # Need to rebuild this function to ignore the 'self' attribute
            @wraps(self.function)
            def final_func(self_, *args):
                return cfunc(*args)

            # replace class named method with c call
            setattr(cls, name, final_func)

    return DllCall


def static_c_call(cname):
    """
        Decorator. Convert a function into call into the class associated dll.
    """

    class DllCall:
        def __init__(self, function):
            self.function = function

        # This gets called when the class is finalized
        def __set_name__(self, cls, name):
            if 'CDDS_NO_IMPORT_LIBS' in os.environ:
                return

            s = inspect.signature(self.function)

            # Set c function types based on python type annotations
            cfunc = getattr(cls._dll_handle, cname)

            # Note: in python 3.10 we get NoneType for voids instead of None
            # This confuses ctypes a lot, so we explicitly test for it
            # We also add the ignore for the error that flake8 generates
            cfunc.restype = s.return_annotation if s.return_annotation != type(None) else None  # noqa: E721

            # Note: ignoring the 'self' argument
            cfunc.argtypes = [p.annotation for i, p in enumerate(s.parameters.values()) if i > 0]

            @wraps(self.function)
            def final_func(*args):
                return cfunc(*args)

            # replace class named method with c call
            setattr(cls, name, final_func)

    return DllCall


def c_callable(return_type, argument_types):
    """
        Decorator. Make a C function type based on python type annotations.
    """
    return ct.CFUNCTYPE(return_type, *argument_types)


class DDS:
    """
        Common class for all DDS related classes. This class enables the c_call magic.
    """
    _dll_handle = load_cyclonedds()

    def __init__(self, reference: int) -> None:
        self._ref = reference


@dataclass
class SampleInfo:
    sample_state: int
    view_state: int
    instance_state: int
    valid_data: bool
    source_timestamp: int
    instance_handle: int
    publication_handle: int
    disposed_generation_count: int
    no_writers_generation_count: int
    sample_rank: int
    generation_rank: int
    absolute_generation_rank: int

class SupportsSerialization(Protocol):
    _U = TypeVar("_U")
    sample_info: Optional[SampleInfo]

    def serialize(self: _U) -> bytes: ...
    @classmethod
    def deserialize(cls: Type[_U], data: bytes) -> _U: ...
