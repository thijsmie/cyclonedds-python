from dataclasses import dataclass

from cyclonedds.idl import IdlStruct
from cyclonedds.idl.types import array, sequence


@dataclass
class Integer(IdlStruct):
    seq: int
    keyval: int

    @classmethod
    def postfix(cls):
        return "integer"


@dataclass
class String(IdlStruct):
    seq: int
    keyval: str

    @classmethod
    def postfix(cls):
        return "string"


@dataclass
class IntArray(IdlStruct):
    seq: int
    keyval: array[int, 3]

    @staticmethod
    def size():
        return 3

    @classmethod
    def postfix(cls):
        return "int_array"


@dataclass
class StrArray(IdlStruct):
    seq: int
    keyval: array[str, 5]

    @staticmethod
    def size():
        return 5

    @classmethod
    def postfix(cls):
        return "str_array"


@dataclass
class IntSequence(IdlStruct):
    seq: int
    keyval: sequence[int]

    @classmethod
    def postfix(cls):
        return "int_sequence"


@dataclass
class StrSequence(IdlStruct):
    seq: int
    keyval: sequence[str, 100]  # max 100 string elements

    @classmethod
    def postfix(cls):
        return "str_sequence"


datatypes = [Integer, String, IntArray, StrArray, IntSequence, StrSequence]
