.. _work_with_qos:

Working with Qos
================

Quality of Service policies, or just Qos for short, are at the core of DDS. While we want to pretend not to know about any networking while writing applications there are often still certain requirements that need to be imposed on the delivery, storage and timing of messages. Qos policies allow you to to express those requirements neatly while still not having to worry about how they are achieved[#]_.

.. [#] Sadly DDS is still bound by the hardware it is running on and the laws of physics, so if you are going to apply a deadline of 1 millisecond to data of several gigabytes you are going to have a bad time.

Immutability
------------

In CycloneDDS-Python Policies are grouped under a Qos object. The Qos object is immutable, meaning you can't add or remove Qos policies once you created it. This is imposed to avoid confusion about which policies are applied on which object. Consider the following (non-functional) code:

.. code-block:: python3
    :linenos:

    qos = Qos(Policy.Durability.Transient)
    sub = Subscriber(dp, qos=qos)

    qos.add(Policy.History.KeepAll)

    sub.get_qos().add(Policy.Reliability.Reliable)

Is the history policy also applied to the subscriber or not? You might doubt for a second here. The second case is even less clear, getting a Qos object directly from the Subscriber and then adding a Policy to it might lead you to conclude it was added to the Subscriber while it in fact was not. So this 'add' is not allowed. However, composing new Qos objects by 'inheriting' and overwriting other Qos objects still make them flexible.

Composing Qos
-------------

You can pass any number of policies when creating a Qos object, as long as they have no overlap. This prevents you from making simple mistakes, such as having two Durability policies in a single Qos.

The Qos constructor also takes a 'base' keyword argument. This means the new Qos object will inherit all policies from the base Qos, except those you overwrite.

Inspecting Qos
--------------

The Qos object behaves mostly like a python ``set`` with some extra bells and whistles. You can compare Qos objects with each other, check if a Policy appears in the Qos, iterate and index and get a readable description.

Indexing needs a special mention, because the keys you can use are the top level Policies.

.. code-block:: python3
    :linenos:

    qos = Qos(Policy.Durability.Transient)
    assert qos[Policy.Durability] == Policy.Durability.Transient


.. _policies:

Policies
========

We list all supported Qos policies in CycloneDDS-Python. The descriptions of the policies are a work in progress and contributions are very welcome.

The policies can be roughly grouped into five categories: Data Availability, Data Delivery, Data Timeliness, Resources and Configuration. We will go through these categories in that order. Please note that even cross-category policies can have interactions. These interactions will be listed where relevant.

Data Availability
*****************


.. _policy_durability:

Durability
----------

The Durability policy has four settings: Volatile, TransientLocal, Transient and Persistent. It can be set on Topics, DataReaders and DataWriters and is set to Volatile by default. It controls how data remains available in the DDS Domain. When the Durability is Volatile no samples are kept for late-joiners. In case it is TransientLocal the samples will be kept locally on the DataWriters side and retransmitted to late joiners. In case of Transient the samples will be kept outside of the local scope and Persistent does that but also makes sure the samples are stored somewhere on disk to ensure they survive a system restart.

Exactly how many samples are kept is dependent on several other policies. Most directly the Lifespan policy, coming up next in the list. Next on the History policy, which can limit the amount of samples kept. Then the ResourceLimits policy which can limit the storage available. In case the Durability is Transient of Persistent you may also need the DurabilityService policy.

The Durability of a DataWriter is *compatible* with DataReaders with equal or lower Durability policies. This means a Transient DataWriter is compatible with Transient, TransientLocal and Volatile DataReaders but a Volatile DataWriter is only compatible with a Volatile DataReader, not with TransientLocal, Transient or Persistent ones.


.. _policy_lifespan:

Lifespan
--------

The Lifespan policy contains just a single number to control. The policy can be set on Topics and DataWriters and is set to 'infinite' by default. It controls how long a sample remains valid. If this policy is set a DataWriter will set an expiration timestamp on every sample as it is being written. If the sample expires it is deleted and not delivered to any DataReaders anymore, no matter if it is kept in a History cache or Durability store.

The Lifespan policy still applies when combined with a History policy and in this way 'overrides' the History policy.

You can change the Lifespan policy on an existing DataWriter. It will not apply to samples written in the past, only to all new samples written from this point.

The Lifespan policy cannot cause any Qos incompatibilities.


.. _policy_history:

History
-------

The History policy has two settings: KeepAll and KeepLast. It can be set on Topics, DataReaders and DataWriters and is set to KeepLast(1) by default. It controls the amount of samples that remain accessible per "group of samples". What constitutes a group depends on the context: for a keyless Topic DataWriter it is all samples it wrote, for a keyed Topic DataWriter it is on a per-instance basis. This policy does not specify a hard requirement but more of a recommendation, as the actual amount of samples available will be limited by the ResourceLimits and Lifespan policies and what is available on the network.

The History policy is local to the DataReader or DataWriter and cannot cause any Qos incompatibilities. Applying it to a Topic is purely for ease of use: it doesn't do anything to the Topic itself apart from passing the History policy you set to the DataReaders and DataWriters you create from it.


Data Delivery
*************

.. _policy_reliablity:

Reliability
-----------

The Reliability policy has two settings: BestEffort and Reliable. It can be set on Topics, DataReaders and DataWriters and is set to BestEffort by default. In BestEffort mode CycloneDDS makes no attempt to verify that data you are writing is actually received by the readers. This is fine for applications that don't mind the occasional dropped message due to, for example, some packet loss on a wireless network. However, if it is important that all data arrives at the reader you can switch the Reliability to Reliable. This comes at a price, since it requires Eclipse CycloneDDS to do bookkeeping on the state of messages. This results in an increase in CPU and Memory usage and requires more network bandwidth.

The Reliable setting has a parameter: max_blocking time. This only applies to the DataWriter side. It can happen that due to resource limits a sample cannot be written yet since buffers are full and no memory can be freed up since CycloneDDS is still waiting for acknowledgements from readers. The write call will then block for a maximum of max_blocking_time. If this elapses and the sample could not be written a DDSException with code DDS_RETCODE_TIMEOUT is raised.

A Reliable DataWriter is *compatible* with a BestEffort DataReader. A BestEffort DataWriter is *incompatible* with a Reliable DataWriter.

.. _policy_resourcelimits:


Resources
*********

ResourceLimits
--------------

The ResourceLimits policy has no settings but three parameters: ``max_samples``, ``max_instances`` and ``max_samples_per_instance``. It can be set on Topics, DataReaders and DataWriters. All parameters are integers and set to ``-1`` by default, which indicates infinite. Infinite here is still limited by available memory and maximum queue sizes in Cyclone DDS.

This policy imposes a hard limit on how much memory may be allocated to store samples per DataWriter or DataReader.

This policy is local to the DataReader or DataWriter and cannot cause any Qos incompatibilities. Applying it to a Topic is purely for ease of use: it doesn't do anything to the Topic itself apart from passing the History policy you set to the DataReaders and DataWriters you create from it.

"Policy.PresentationAccessScope.Instance": Policy.PresentationAccessScope.Instance,
"Policy.PresentationAccessScope.Topic": Policy.PresentationAccessScope.Topic,
"Policy.PresentationAccessScope.Group": Policy.PresentationAccessScope.Group,
"Policy.Lifespan": Policy.Lifespan,
"Policy.Deadline": Policy.Deadline,
"Policy.LatencyBudget": Policy.LatencyBudget,
"Policy.Ownership.Shared": Policy.Ownership.Shared,
"Policy.Ownership.Exclusive": Policy.Ownership.Exclusive,
"Policy.OwnershipStrength": Policy.OwnershipStrength,
"Policy.Liveliness.Automatic": Policy.Liveliness.Automatic,
"Policy.Liveliness.ManualByParticipant": Policy.Liveliness.ManualByParticipant,
"Policy.Liveliness.ManualByTopic": Policy.Liveliness.ManualByTopic,
"Policy.TimeBasedFilter": Policy.TimeBasedFilter,
"Policy.Partition": Policy.Partition,
"Policy.TransportPriority": Policy.TransportPriority,
"Policy.DestinationOrder.ByReceptionTimestamp": Policy.DestinationOrder.ByReceptionTimestamp,
"Policy.DestinationOrder.BySourceTimestamp": Policy.DestinationOrder.BySourceTimestamp,
"Policy.WriterDataLifecycle": Policy.WriterDataLifecycle,
"Policy.ReaderDataLifecycle": Policy.ReaderDataLifecycle,
"Policy.DurabilityService": Policy.DurabilityService,
"Policy.IgnoreLocal.Nothing": Policy.IgnoreLocal.Nothing,
"Policy.IgnoreLocal.Participant": Policy.IgnoreLocal.Participant,
"Policy.IgnoreLocal.Process": Policy.IgnoreLocal.Process,
"Policy.Userdata": Policy.Userdata,
"Policy.Groupdata": Policy.Groupdata,
"Policy.Topicdata": Policy.Topicdata