from cyclonedds.core import Qos, Policy
from cyclonedds.domain import DomainParticipant
from cyclonedds.topic import Topic
from cyclonedds.pub import Publisher, DataWriter
from cyclonedds.sub import Subscriber, DataReader
from cyclonedds.util import duration
from cyclonedds.idl import IdlStruct

from dataclasses import dataclass
from time import sleep


@dataclass
class Message(IdlStruct):
    message: str


class Common:
    def __init__(self, domain_id=0):
        self.qos = Qos(Policy.Reliability.Reliable(duration(seconds=2)), Policy.History.KeepLast(10))

        self.dp = DomainParticipant(domain_id)
        self.tp = Topic(self.dp, 'Message', Message)
        self.pub = Publisher(self.dp)
        self.sub = Subscriber(self.dp)
        self.dw = DataWriter(self.pub, self.tp, qos=self.qos)
        self.dr = DataReader(self.sub, self.tp, qos=self.qos)
        self.msg = Message(message="hi")
        self.msg2 = Message(message="hi2")

def communication_basic_read(common_setup):
    print("entry_rd")
    msg = Message(message="Hi!")
    common_setup.dw.write(msg)
    result = common_setup.dr.read()

    assert len(result) == 1
    assert result[0] == msg
    print("exit_rd")

def communication_basic_take(common_setup):
    msg = Message(message="Hi!")
    common_setup.dw.write(msg)
    result = common_setup.dr.take()

    assert len(result) == 1
    assert result[0] == msg

def mjester():
    communication_basic_read(Common())
    sleep(1)
    communication_basic_read(Common())
    sleep(1)
    communication_basic_read(Common())
    sleep(1)
    communication_basic_take(Common())
    sleep(1)

print("Running")
mjester()
print("Exit")