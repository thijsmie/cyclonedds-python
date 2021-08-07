from dataclasses import dataclass

from cyclonedds.idl import IdlStruct
from cyclonedds.idl.types import int32
from cyclonedds.idl.annotations import key


@dataclass
class replybytes(IdlStruct, typename="py_c_compat.replybytes"):
    data: bytes


@dataclass
class tp_long(IdlStruct, typename="py_c_compat.tp_long"):
    data: int32
    key(data)
