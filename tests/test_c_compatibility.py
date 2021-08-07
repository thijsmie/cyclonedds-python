import os
import asyncio
import concurrent.futures

from cyclonedds.core import Entity
from cyclonedds.domain import DomainParticipant
from cyclonedds.topic import Topic
from cyclonedds.pub import DataWriter
from cyclonedds.sub import DataReader

from test_c_compatibility_classes import tp_long, replybytes


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


import time
def test_c_compat():
    #virtualenv.run("pip install " + os.path.join(os.path.dirname(__file__), "py_c_compat"))

    dp = DomainParticipant()
    time.sleep(2)
    stp = Topic(dp, "tp_long", tp_long)
    wr = DataWriter(dp, stp)
    time.sleep(10)
    rtp = Topic(dp, "KeyBytes", replybytes)
    rd = DataReader(dp, rtp)
    wr.write(tp_long(12))
    time.sleep(10)
    return
    async def run(writer):
        writer.write(tp_long(12))

    ddsc = os.path.join(os.environ["CYCLONEDDS_HOME"], "lib/libddsc.so.0")
    run_cmd_concurrent(virtualenv, f"LD_PRELOAD={ddsc} republisher tp_long", run, (wr,))

    print(rd.read())