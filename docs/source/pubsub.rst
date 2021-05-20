.. _pubsub:

Publishing and Subscribing
==========================

The core of any DDS application is the ability to send data by means of a publishing and receiving data by subscribing. To perform these actions in CycloneDDS-Python we need to do some setup universal to all DDS applications, no matter which language they are written in or implementation that they use: Participate in a Domain, create a Publisher or Subscriber and then create a DataWriter or Reader. We will start by writing a simple publishing application that writes data from a hypothetical temperature sensor. Our mock temperature sensor is defined as follows:


.. code-block:: python
    :linenos:

    import random


    class TemperatureSensor:
        def __init__(self, id: int):
            self.id: int = id
            self.temp: float = 22.0

        def measure(self) -> float:
            self.temp += random.randrange(-1.0, 1.0)
            return self.temp


    sensor = TemperatureSensor(12002)


Now that we have defined the temperature sensor we have to think about how to represent the data on the network. We learned in :ref:`datatypes` how to make a struct and add fields to it. We do this for a temperature measurement:

.. code-block:: python
    :linenos:

    from pycdr import cdr


    @cdr(keylist=["sensor_id"])
    class TemperatureMeasurement:
        sensor_id: int
        measurement: float


    def measurement_message(sensor: TemperatureSensor) -> TemperatureMeasurement:
        return TemperatureMeasurement(
            sensor_id=sensor.id,
            measurement=sensor.measure()
        )


I also added a little utility function to create the data object for us to avoid clutter in later code.