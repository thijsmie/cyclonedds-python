import pytest

from cyclonedds.core import Statistics
from cyclonedds.domain import DomainParticipant
from cyclonedds.topic import Topic
from cyclonedds.sub import Subscriber, DataReader
from cyclonedds.pub import Publisher, DataWriter

from testtopics import Message

def test_create_statistics():
    dp = DomainParticipant(0)
    tp = Topic(dp, "blah", Message)
    dw = DataWriter(dp, tp)
    stat = Statistics(dw)
    print(stat)
    print(stat.data)
    assert stat.data
