import pytest

from cyclonedds.core import Statistics
from cyclonedds.domain import DomainParticipant
from cyclonedds.topic import Topic
from cyclonedds.sub import Subscriber, DataReader
from cyclonedds.pub import Publisher, DataWriter


def test_create_statistics():
    dp = DomainParticipant(0)
    assert Statistics(dp) is not None
