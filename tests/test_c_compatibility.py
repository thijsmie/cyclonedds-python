import os
import time
import sys
import asyncio
import subprocess
import concurrent.futures

from cyclonedds.core import Entity, WaitSet, ReadCondition, SampleState, ViewState, InstanceState
from cyclonedds.qos import Qos, Policy
from cyclonedds.domain import DomainParticipant
from cyclonedds.topic import Topic
from cyclonedds.pub import DataWriter
from cyclonedds.sub import DataReader
from cyclonedds.util import duration

from test_c_compatibility_classes import replybytes
from random_instance import generate_random_instance
from cyclonedds._clayer import ddspy_calc_key


async def _run_cmd_concurrent(virtualenv, vargs, runner, runargs):
    loop = asyncio.get_event_loop_policy().get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        task = loop.run_in_executor(pool, virtualenv.run, vargs)
        await asyncio.sleep(0.3)
        test = await runner(*runargs)
        return (await task), test


def run_cmd_concurrent(virtualenv, vargs, runner, runargs):
    return asyncio.get_event_loop_policy().get_event_loop().run_until_complete(
        _run_cmd_concurrent(virtualenv, vargs, runner, runargs)
    )


NUM_SAMPLES = 50
def test_c_compat(virtualenv_with_py_c_compat):
    sys.path.insert(0, os.path.join(virtualenv_with_py_c_compat.dir, "lib", "site-packages"))
    print(virtualenv_with_py_c_compat.dir)
    import fuzzymod

    for name in virtualenv_with_py_c_compat.typenames:
        subproc: subprocess.Popen = virtualenv_with_py_c_compat.run(
            ["republisher", name, str(NUM_SAMPLES)], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        datatype = getattr(fuzzymod, name)
        samples = [generate_random_instance(datatype, seed=i) for i in range(NUM_SAMPLES)]

        dp = DomainParticipant()

        time.sleep(0.2)
        rtp = Topic(dp, "replybytes", replybytes)
        rd = DataReader(dp, rtp)
        rc = ReadCondition(rd, ViewState.Any | InstanceState.Any | SampleState.NotRead)
        w = WaitSet(dp)
        w.attach(rc)
        time.sleep(0.2)
        stp = Topic(dp, name, datatype)
        wr = DataWriter(dp, stp)

        i = None
        samp = None
        sent = None
        try:
            for i in range(NUM_SAMPLES):
                sent = samples[samp.seq]
                wr.write(sent)
                w.wait(timeout=duration(seconds=2))
                samp = rd.read(condition=rc)[0]
                assert samp.data == ddspy_calc_key(datatype.__idl__, sent.serialize()) == datatype.__idl__.key(sent)
        except Exception as e:
            print("datatype:", datatype)
            print("i:", i)
            print("sample:", sent)
            print("recv:", samp.data if samp else None)
            print("keyvm:", ddspy_calc_key(datatype.__idl__, sent.serialize()))
            print("pymachine:", datatype.__idl__.key(sent))
            raise e

        subproc.communicate(timeout=2.0)
        assert subproc.returncode == 0
