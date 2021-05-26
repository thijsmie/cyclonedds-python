import ctypes as ct
import uuid

from typing import TYPE_CHECKING

if not TYPE_CHECKING:
    # Monkeypatch typed pointer from typeshed into ctypes
    class pointer:
        @classmethod
        def __class_getitem__(cls, item):
            return ct.POINTER(item)
    ct.pointer = pointer


entity = ct.c_int32
time = ct.c_int64
duration = ct.c_int64
instance_handle = ct.c_int64
domainid = ct.c_uint32
sample_state = ct.c_int
view_state = ct.c_int
instance_state = ct.c_int
reliability = ct.c_int
durability = ct.c_int
history = ct.c_int
presentation_access_scope = ct.c_int
ingnorelocal = ct.c_int
ownership = ct.c_int
liveliness = ct.c_int
destination_order = ct.c_int
qos_p = ct.c_void_p
attach = ct.c_void_p
listener_p = ct.c_void_p
topic_descriptor_p = ct.c_void_p
returnv = ct.c_int32


class inconsistent_topic_status(ct.Structure):  # noqa N801
    _fields_ = [('total_count', ct.c_uint32),
                ('total_count_change', ct.c_int32)]

class liveliness_lost_status(ct.Structure):  # noqa N801
    _fields_ = [('total_count', ct.c_uint32),
                ('total_count_change', ct.c_int32)]

class liveliness_changed_status(ct.Structure):  # noqa N801
    _fields_ = [('alive_count', ct.c_uint32),
                ('not_alive_count', ct.c_uint32),
                ('alive_count_change', ct.c_int32),
                ('not_alive_count_change', ct.c_int32),
                ('last_publication_handle', ct.c_int64)]

class offered_deadline_missed_status(ct.Structure):  # noqa N801
    _fields_ = [('total_count', ct.c_uint32),
                ('total_count_change', ct.c_int32),
                ('last_instance_handle', ct.c_int64)]

class offered_incompatible_qos_status(ct.Structure):  # noqa N801
    _fields_ = [('total_count', ct.c_uint32),
                ('total_count_change', ct.c_int32),
                ('last_policy_id', ct.c_uint32)]

class sample_lost_status(ct.Structure):  # noqa N801
    _fields_ = [('total_count', ct.c_uint32),
                ('total_count_change', ct.c_int32)]

class sample_rejected_status(ct.Structure):  # noqa N801
    _fields_ = [('total_count', ct.c_uint32),
                ('total_count_change', ct.c_int32),
                ('last_reason', ct.c_int),
                ('last_instance_handle', ct.c_int64)]

class requested_deadline_missed_status(ct.Structure):  # noqa N801
    _fields_ = [('total_count', ct.c_uint32),
                ('total_count_change', ct.c_int32),
                ('last_instance_handle', ct.c_int64)]

class requested_incompatible_qos_status(ct.Structure):  # noqa N801
    _fields_ = [('total_count', ct.c_uint32),
                ('total_count_change', ct.c_int32),
                ('last_policy_id', ct.c_uint32)]

class publication_matched_status(ct.Structure):  # noqa N801
    _fields_ = [('total_count', ct.c_uint32),
                ('total_count_change', ct.c_int32),
                ('current_count', ct.c_uint32),
                ('current_count_change', ct.c_int32),
                ('last_subscription_handle', ct.c_int64)]

class subscription_matched_status(ct.Structure):  # noqa N801
    _fields_ = [('total_count', ct.c_uint32),
                ('total_count_change', ct.c_int32),
                ('current_count', ct.c_uint32),
                ('current_count_change', ct.c_int32),
                ('last_publication_handle', ct.c_int64)]

class guid(ct.Structure):  # noqa N801
    _fields_ = [('v', ct.c_uint8 * 16)]

    def as_python_guid(self) -> uuid.UUID:
        return uuid.UUID(bytes=bytes(self.v))

class sample_info(ct.Structure):  # noqa N801
    _fields_ = [
        ('sample_state', ct.c_uint),
        ('view_state', ct.c_uint),
        ('instance_state', ct.c_uint),
        ('valid_data', ct.c_bool),
        ('source_timestamp', ct.c_int64),
        ('instance_handle', ct.c_uint64),
        ('publication_handle', ct.c_uint64),
        ('disposed_generation_count', ct.c_uint32),
        ('no_writers_generation_count', ct.c_uint32),
        ('sample_rank', ct.c_uint32),
        ('generation_rank', ct.c_uint32),
        ('absolute_generation_rank', ct.c_uint32)
    ]

class sample_buffer(ct.Structure):  # noqa N801
    _fields_ = [
        ('buf', ct.c_void_p),
        ('len', ct.c_size_t)
    ]
