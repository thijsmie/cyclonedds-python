from dataclasses import dataclass
from cyclonedds.idl import IdlStruct
from cyclonedds.domain import DomainParticipant
from cyclonedds.pub import DataWriter
from cyclonedds.sub import DataReader
from cyclonedds.topic import Topic

from support_modules.testtopics import InheritanceTestChild


@dataclass
class A(IdlStruct):
    fa: int


@dataclass
class B(A):
    fb: int


def test_inheritance():
    v = B(fa=1, fb=2)
    assert v == B.deserialize(v.serialize())


def test_inheritance_readwrite():
    dp = DomainParticipant()
    tp = Topic(dp, "Hello", InheritanceTestChild)
    dw = DataWriter(dp, tp)
    dr = DataReader(dp, tp)
    sample = InheritanceTestChild(var='1', var2='2')
    dw.write(sample)
    sample_read = dr.read()[0]
    assert sample == sample_read
