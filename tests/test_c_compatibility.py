import os
import time
import asyncio
import importlib.util
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


def test_c_compat(virtualenv_with_py_c_compat):
    fuzzymod_spec = importlib.util.spec_from_file_location(
        "fuzzymod",
        os.path.join(virtualenv_with_py_c_compat.dir.name, "lib", "site-packages", "fuzzymod")
    )
    fuzzymod = importlib.util.module_from_spec(fuzzymod_spec)
    fuzzymod_spec.loader.exec_module(fuzzymod)

    for name in virtualenv_with_py_c_compat.names:
        subproc: subprocess.Popen = virtualenv_with_py_c_compat.run(
            ["republisher", name], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        datatype = getattr(fuzzymod, name)
        dp = DomainParticipant()

        time.sleep(0.5)
        rtp = Topic(dp, "replybytes", replybytes)
        rd = DataReader(dp, rtp)
        rc = ReadCondition(rd, ViewState.Any | InstanceState.Any | SampleState.Any)
        w = WaitSet(dp)
        w.attach(rc)

        time.sleep(0.5)
        stp = Topic(dp, name, datatype)
        wr = DataWriter(dp, stp)
        sent = generate_random_instance(datatype)
        wr.write(sent)

        w.wait(timeout=duration(seconds=16))
        samp = rd.read(condition=rc)[0]
        assert samp.data == ddspy_calc_key(datatype.__idl__, sent.serialize())

        subproc.communicate(timeout=2.0)
        assert subproc.returncode == 0
