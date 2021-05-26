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

import uuid
import asyncio
import concurrent
import ctypes as ct
from dataclasses import dataclass
from typing import Optional, Union, Generic, TypeVar, Generator, AsyncGenerator, TYPE_CHECKING

from .core import Entity, Listener, DDSException, Qos, ReadCondition, ViewState, InstanceState, SampleState, \
    _Condition, WaitSet
from .internal import c_call, dds_c_t
from .qos import Qos, _CQos
from .util import duration

from ddspy import ddspy_read_participant, ddspy_take_participant, ddspy_read_endpoint, ddspy_take_endpoint


if TYPE_CHECKING:
    import cyclonedds


@dataclass
class DcpsParticipant:
    """
    Data sample as returned when you subscribe to the BuiltinTopicDcpsParticipant topic.

    Attributes
    ----------
    key: uuid.UUID
        Unique participant identifier
    qos: Qos
        Qos policies associated with the participant.
    """

    key: uuid.UUID
    qos: Qos


@dataclass
class DcpsEndpoint:
    """
    Data sample as returned when you subscribe to the BuiltinTopicDcpsTopic,
    BuiltinTopicDcpsPublication or BuiltinTopicDcpsSubscription topic.

    Attributes
    ----------
    key: uuid.UUID
        Unique identifier for the topic, publication or subscription endpoint.
    participant_key: uuid.UUID
        Unique identifier of the participant the endpoint belongs to.
    participant_instance_handle: int
        Instance handle
    topic_name: str
        Name of the associated topic.
    type_name: str
        Name of the type.
    qos: Qos
        Qos policies associated with the endpoint.
    """
    key: uuid.UUID
    participant_key: uuid.UUID
    participant_instance_handle: int
    topic_name: str
    type_name: str
    qos: Qos


_T = TypeVar("_T", DcpsParticipant, DcpsEndpoint)


class BuiltinTopic(Generic[_T]):
    """ Represent a built-in CycloneDDS Topic by magic reference number. """
    def __init__(self, _ref, data_type):
        self._ref = _ref
        self.data_type = data_type

    def __del__(self):
        pass


class BuiltinDataReader(Entity, Generic[_T]):
    """
    Builtin topics have sligtly different behaviour than normal topics, so you should use this BuiltinDataReader
    instead of the normal DataReader. They are identical in the rest of their functionality.
    """
    def __init__(self,
                 subscriber_or_participant: Union['cyclonedds.sub.Subscriber', 'cyclonedds.domain.DomainParticipant'],
                 builtin_topic: BuiltinTopic[_T],
                 qos: Optional[Qos] = None,
                 listener: Optional[Listener] = None) -> None:
        """Initialize the BuiltinDataReader

        Parameters
        ----------
        subscriber_or_participant: cyclonedds.sub.Subscriber, cyclonedds.domain.DomainParticipant
            The subscriber to which this reader will be added. If you supply a DomainParticipant a subscriber will be created for you.

        builtin_topic: cyclonedds.builtin.BuiltinTopic
            Which Builtin Topic to subscribe to. This can be one of BuiltinTopicDcpsParticipant, BuiltinTopicDcpsTopic,
            BuiltinTopicDcpsPublication or BuiltinTopicDcpsSubscription. Please note that BuiltinTopicDcpsTopic will fail if
            you built CycloneDDS without Topic Discovery.
        qos: cyclonedds.core.Qos, optional = None
            Optionally supply a Qos.
        listener: cyclonedds.core.Listener = None
            Optionally supply a Listener.
        """
        self._topic: BuiltinTopic[_T] = builtin_topic

        cqos = _CQos.qos_to_cqos(qos) if qos else None
        Entity.__init__(
            self,
            self._create_reader(
                subscriber_or_participant._ref,
                builtin_topic._ref,
                cqos,
                listener._ref if listener else None
            )
        )
        self._next_condition = ReadCondition(self, ViewState.Any | SampleState.NotRead | InstanceState.Any)
        if cqos:
            _CQos.cqos_destroy(cqos)
        self._make_constructors()

    def _make_constructors(self):
        def participant_constructor(keybytes, qosobject, sampleinfo):
            s = DcpsParticipant(uuid.UUID(bytes=keybytes), qos=qosobject)
            s.sample_info = sampleinfo
            return s

        def endpoint_constructor(keybytes, participant_keybytes, p_instance_handle, topic_name, type_name, qosobject, sampleinfo):
            s = DcpsEndpoint(
                uuid.UUID(bytes=keybytes),
                uuid.UUID(bytes=participant_keybytes),
                p_instance_handle,
                topic_name,
                type_name,
                qosobject
            )
            s.sample_info = sampleinfo
            return s

        def cqos_to_qos(pointer):
            p = ct.cast(pointer, dds_c_t.qos_p)
            return _CQos.cqos_to_qos(p)

        if self._topic == BuiltinTopicDcpsParticipant:
            self._readfn = ddspy_read_participant
            self._takefn = ddspy_take_participant
            self._constructor = participant_constructor
        else:
            self._readfn = ddspy_read_endpoint
            self._takefn = ddspy_take_endpoint
            self._constructor = endpoint_constructor
        self._cqos_conv = cqos_to_qos

    def read(self, N: int = 1, condition: Optional[_Condition] = None):
        """Read a maximum of N samples, non-blocking. Optionally use a read/query-condition to select which samples
        you are interested in.

        Parameters
        ----------
        N: int
            The maximum number of samples to read.
        condition: cyclonedds.core.ReadCondition, cyclonedds.core.QueryCondition, optional
            Only read samples that satisfy the supplied condition.

        Raises
        ------
        DDSException
            If any error code is returned by the DDS API it is converted into an exception.
        """

        ref = condition._ref if condition else self._ref
        ret = self._readfn(ref, N, self._constructor, self._cqos_conv)

        if type(ret) == int:
            raise DDSException(ret, f"Occurred when calling read() in {repr(self)}")

        return ret

    def take(self, N: int = 1, condition=None):
        """Take a maximum of N samples, non-blocking. Optionally use a read/query-condition to select which samples
        you are interested in.

        Parameters
        ----------
        N: int
            The maximum number of samples to read.
        condition: cyclonedds.core.ReadCondition, cyclonedds.core.QueryCondition, optional
            Only take samples that satisfy the supplied condition.

        Raises
        ------
        DDSException
            If any error code is returned by the DDS API it is converted into an exception.
        """
        ref = condition._ref if condition else self._ref
        ret = self._takefn(ref, N, self._constructor, self._cqos_conv)

        if type(ret) == int:
            raise DDSException(ret, f"Occurred when calling read() in {repr(self)}")

        return ret

    def read_next(self) -> Optional[_T]:
        """Shortcut method to read exactly one sample or return None.

        Raises
        ------
        DDSException
            If any error code is returned by the DDS API it is converted into an exception.
        """
        self._next_condition = self._next_condition or \
            ReadCondition(self, ViewState.Any | SampleState.NotRead | InstanceState.Any)
        samples = self.read(condition=self._next_condition)
        if samples:
            return samples[0]
        return None

    def take_next(self) -> Optional[_T]:
        """Shortcut method to take exactly one sample or return None.

        Raises
        ------
        DDSException
            If any error code is returned by the DDS API it is converted into an exception.
        """
        self._next_condition = self._next_condition or \
            ReadCondition(self, ViewState.Any | SampleState.NotRead | InstanceState.Any)
        samples = self.take(condition=self._next_condition)
        if samples:
            return samples[0]
        return None

    def read_iter(self, condition: _Condition = None, timeout: int = None) -> Generator[_T, None, None]:
        """Shortcut method to iterate reading samples. Iteration will stop once the timeout you supply expires.
        Every time a sample is received the timeout is reset.

        Raises
        ------
        DDSException
            If any error code is returned by the DDS API it is converted into an exception.
        """
        assert self.participant is not None
        waitset = WaitSet(self.participant)
        condition = ReadCondition(self, ViewState.Any | InstanceState.Any | SampleState.NotRead)
        waitset.attach(condition)
        timeout = timeout or duration(weeks=99999)

        while True:
            while True:
                a = self.read(condition=condition)
                if not a:
                    break
                yield a[0]
            if waitset.wait(timeout) == 0:
                break

    def take_iter(self, condition: _Condition = None, timeout: int = None) -> Generator[_T, None, None]:
        """Shortcut method to iterate taking samples. Iteration will stop once the timeout you supply expires.
        Every time a sample is received the timeout is reset.

        Raises
        ------
        DDSException
            If any error code is returned by the DDS API it is converted into an exception.
        """
        assert self.participant is not None
        waitset = WaitSet(self.participant)
        condition = condition or ReadCondition(self, ViewState.Any | InstanceState.Any | SampleState.NotRead)
        waitset.attach(condition)
        timeout = timeout or duration(weeks=99999)

        while True:
            while True:
                a = self.take(condition=condition)
                if not a:
                    break
                yield a[0]
            if waitset.wait(timeout) == 0:
                break

    async def read_aiter(self, condition: _Condition = None, timeout: int = None) -> AsyncGenerator[_T, None]:
        """Shortcut method to asycn iterate reading samples. Iteration will stop once the timeout you supply expires.
        Every time a sample is received the timeout is reset.

        Raises
        ------
        DDSException
            If any error code is returned by the DDS API it is converted into an exception.
        """
        assert self.participant is not None
        waitset = WaitSet(self.participant)
        condition = condition or ReadCondition(self, ViewState.Any | InstanceState.Any | SampleState.NotRead)
        waitset.attach(condition)
        timeout = timeout or duration(weeks=99999)

        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            while True:
                while True:
                    a = self.read(condition=condition)
                    if not a:
                        break
                    yield a[0]
                result = await loop.run_in_executor(pool, waitset.wait, timeout)
                if result == 0:
                    break

    async def take_aiter(self, condition: _Condition = None, timeout: int = None) -> AsyncGenerator[_T, None]:
        """Shortcut method to asycn iterate taking samples. Iteration will stop once the timeout you supply expires.
        Every time a sample is received the timeout is reset.

        Raises
        ------
        DDSException
            If any error code is returned by the DDS API it is converted into an exception.
        """
        assert self.participant is not None
        waitset = WaitSet(self.participant)
        condition = condition or ReadCondition(self, ViewState.Any | InstanceState.Any | SampleState.NotRead)
        waitset.attach(condition)
        timeout = timeout or duration(weeks=99999)

        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            while True:
                while True:
                    a = self.take(condition=condition)
                    if not a:
                        break
                    yield a[0]
                result = await loop.run_in_executor(pool, waitset.wait, timeout)
                if result == 0:
                    break

    def wait_for_historical_data(self, timeout: int) -> bool:
        ret = self._wait_for_historical_data(self._ref, timeout)

        if ret == 0:
            return True
        elif ret == DDSException.DDS_RETCODE_TIMEOUT:
            return False
        raise DDSException(ret, f"Occured while waiting for historical data in {repr(self)}")

    @c_call("dds_create_reader")
    def _create_reader(self, subscriber: dds_c_t.entity, topic: dds_c_t.entity, qos: dds_c_t.qos_p,
                       listener: dds_c_t.listener_p) -> dds_c_t.entity:
        pass

    @c_call("dds_reader_wait_for_historical_data")
    def _wait_for_historical_data(self, reader: dds_c_t.entity, max_wait: dds_c_t.duration) -> dds_c_t.returnv:
        pass


_pseudo_handle = 0x7fff0000
BuiltinTopicDcpsParticipant = BuiltinTopic(_pseudo_handle + 1, DcpsParticipant)
"""Built-in topic, is published to when a new participants appear on the network."""

BuiltinTopicDcpsTopic = BuiltinTopic(_pseudo_handle + 2, DcpsEndpoint)
"""Built-in topic, is published to when a new topic appear on the network."""

BuiltinTopicDcpsPublication = BuiltinTopic(_pseudo_handle + 3, DcpsEndpoint)
"""Built-in topic, is published to when a publication happens."""

BuiltinTopicDcpsSubscription = BuiltinTopic(_pseudo_handle + 4, DcpsEndpoint)
"""Built-in topic, is published to when a subscription happens."""

__all__ = [
    "DcpsParticipant", "DcpsEndpoint", "BuiltinDataReader",
    "BuiltinTopicDcpsParticipant", "BuiltinTopicDcpsTopic",
    "BuiltinTopicDcpsPublication", "BuiltinTopicDcpsSubscription"
]
