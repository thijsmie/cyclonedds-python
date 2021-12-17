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
import dataclasses as _dataclasses
from typing import Any, Type, TypeVar, Optional, Dict, Callable, Sequence
from enum import Enum

from .types import ValidUnionHolder
from ._main import IdlMeta, IdlUnionMeta, IdlBitmaskMeta, IdlEnumMeta
from ._support import Buffer, Endianness


_TIS = TypeVar('_TIS', bound='IdlStruct')
_TIU = TypeVar('_TIU', bound='IdlUnion')
_TIB = TypeVar('_TIB', bound='IdlBitmask')
_TIE = TypeVar('_TIE', bound='IdlEnum')


class IdlStruct(metaclass=IdlMeta):
    def serialize(self, buffer: Optional[Buffer] = None, endianness: Optional[Endianness] = None) -> bytes:
        return self.__idl__.serialize(self, buffer=buffer, endianness=endianness)

    @classmethod
    def deserialize(cls: Type[_TIS], data: bytes, has_header: bool = True) -> _TIS:
        return cls.__idl__.deserialize(data, has_header=has_header)


def make_idl_struct(class_name: str, typename: str, fields: Dict[str, Any], *, dataclassify=True,
                    bases=(), field_annotations: Optional[Dict[str, Dict[str, Any]]] = None):
    bases = tuple(list(*bases) + [IdlStruct])
    namespace = IdlMeta.__prepare__(class_name, bases, typename=typename)

    for fieldname, _type in fields.items():
        namespace['__annotations__'][fieldname] = _type

    if field_annotations:
        namespace['__idl_field_annotations__'] = field_annotations

    cls = IdlMeta(class_name, bases, namespace)
    if dataclassify:
        cls = _dataclasses.dataclass(cls)
    return cls


class IdlUnion(metaclass=IdlUnionMeta):
    def __init__(self, **kwargs):
        self.__active = None
        self.__discriminator = None
        self.__value = None

        if len(kwargs) == 2 and 'discriminator' in kwargs and 'value' in kwargs:
            self.set(kwargs['discriminator'], kwargs['value'])
        elif len(kwargs) == 1:
            for key, value in kwargs.items():
                self.__setattr__(key, value)
        else:
            raise ValueError("Can only set one field of union.")

    def __setattr__(self, name: str, value: Any) -> None:
        if name not in self.__idl_names__:
            return super().__setattr__(name, value)

        if self.__idl_default__ and self.__idl_default__[0] == name:
            if self.__active:
                super().__setattr__(self.__active, None)

            self.__active = name
            self.__discriminator = None
            self.__value = value
            return super().__setattr__(name, value)

        for label, case in self.__idl_cases__.items():
            if case[0] == name:
                if self.__active:
                    super().__setattr__(self.__active, None)

                self.__active = name
                self.__discriminator = label
                self.__value = value
                return super().__setattr__(name, value)

        raise Exception("Programmer error, should not get here.")

    def __getattr__(self, name: str) -> Any:
        if name in self.__idl_names__ and not self.__active == name:
            raise AttributeError("Tried to get inactive case on union")
        return super().__getattribute__(name)

    def set(self, discriminator: int, value: Any) -> None:
        if discriminator not in self.__idl_cases__:
            if self.__active:
                super().__setattr__(self.__active, None)

            self.__discriminator = discriminator
            self.__value = value

            if self.__idl_default__:
                self.__active = self.__idl_default__[0]
                return super().__setattr__(self.__idl_default__[0], value)
        else:
            case = self.__idl_cases__[discriminator]
            if self.__active:
                super().__setattr__(self.__active, None)

            self.__active = case[0]
            self.__discriminator = discriminator
            self.__value = value
            return super().__setattr__(case[0], value)

    def get(self):
        return self.__discriminator, self.__value

    @property
    def discriminator(self) -> Optional[int]:
        return self.__discriminator

    @property
    def value(self):
        return self.__value

    def __repr__(self):
        return f"{self.__class__.__name__}[Union]{self.get()}"

    def __rich_repr__(self):
        if self.discriminator is None:
            yield "Default selected", None
        elif self.value is None:
            yield "Default selected", self.discriminator
        else:
            yield "discriminator", self.discriminator
            yield self.__active or "value", self.value

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        if self.discriminator != other.discriminator:
            if self.discriminator is None and other.discriminator != self.__idl_default_discriminator__:
                return False
            if other.discriminator is None and self.discriminator != self.__idl_default_discriminator__:
                return False
        if self.value != other.value:
            return False
        return True

    def serialize(self, buffer: Optional[Buffer] = None, endianness: Optional[Endianness] = None) -> bytes:
        return self.__idl__.serialize(self, buffer=buffer, endianness=endianness)

    @classmethod
    def deserialize(cls: Type[_TIU], data: bytes, has_header: bool = True) -> _TIU:
        return cls.__idl__.deserialize(data, has_header=has_header)


def make_idl_union(class_name: str, typename: str, fields: Dict[str, ValidUnionHolder], *,
                   bases=(), field_annotations: Optional[Dict[str, Dict[str, Any]]] = None):
    bases = tuple(list(*bases) + [IdlUnion])
    namespace = IdlUnionMeta.__prepare__(class_name, bases, typename=typename)

    for fieldname, _type in fields.items():
        namespace['__annotations__'][fieldname] = _type

    if field_annotations:
        namespace['__idl_field_annotations__'] = field_annotations

    return IdlUnionMeta(class_name, bases, namespace)


class IdlBitmask(metaclass=IdlBitmaskMeta):
    @classmethod
    def from_mask(cls: Type[_TIB], mask: int) -> _TIB:
        values = {}
        for fmask, name in cls.__idl_bits__.items():
            values[name] = (mask & fmask) > 0
        return cls(**values)

    def as_mask(self) -> int:
        return sum(mask for mask, name in self.__idl_bits__.items() if getattr(self, name))

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.as_mask() == other.as_mask()


def make_idl_bitmask(class_name: str, typename: str, fields: Sequence[str], *, dataclassify=True,
                     field_annotations: Optional[Dict[str, Dict[str, Any]]] = None):

    namespace = IdlBitmaskMeta.__prepare__(class_name, (IdlBitmask,), typename=typename)

    for fieldname in fields:
        namespace['__annotations__'][fieldname] = bool

    if field_annotations:
        namespace['__idl_field_annotations__'] = field_annotations

    cls = IdlBitmaskMeta(class_name, (IdlBitmask,), namespace)
    if dataclassify:
        cls = _dataclasses.dataclass(cls)
    return cls


class IdlEnum(Enum, metaclass=IdlEnumMeta):
    def _generate_next_value_(name, start, count, last_values):
        return last_values[-1] + 1 if last_values else count


def make_idl_enum(class_name: str, typename: str, fields: Dict[str, int]):
    namespace = IdlEnumMeta.__prepare__(class_name, (IdlEnum,), typename=typename)

    for fieldname, value in fields.items():
        namespace[fieldname] = value

    return IdlEnumMeta(class_name, (IdlEnum,), namespace)


__all__ = [
    "IdlUnion", "IdlStruct", "IdlBitmask", "IdlEnum",
    "make_idl_struct", "make_idl_union", "make_idl_bitmask",
    "make_idl_enum"
]
