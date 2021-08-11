from dataclasses import dataclass

from cyclonedds.idl import IdlStruct
from cyclonedds.idl.types import uint32
from cyclonedds.idl.annotations import key


@dataclass
class replybytes(IdlStruct, typename="py_c_compat.replybytes"):
    reply_to: str
    key(reply_to)
    data: bytes


@dataclass
class tp_long(IdlStruct, typename="py_c_compat.tp_long"):
    data: uint32
    key(data)
