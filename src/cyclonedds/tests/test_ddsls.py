import pytest
import json
import time
import signal

import subprocess

from cyclonedds.domain import DomainParticipant


# Helper functions

def run_ddsls(args, timeout=10):
    ddsls_process = subprocess.Popen(["ddsls.py"] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        stdout, stderr = ddsls_process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as e:
        ddsls_process.kill()
        raise e

    return {
        "stdout": stdout.decode(),
        "stderr": stderr.decode(),
        "status": ddsls_process.returncode
    }


def start_ddsls_watchmode(args):
    ddsls_process = subprocess.Popen(["ddsls.py", "--watch"] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ddsls_process


def stop_ddsls_watchmode(ddsls_process, timeout=10):
    ddsls_process.send_signal(signal.SIGINT)

    try:
        stdout, stderr = ddsls_process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as e:
        ddsls_process.kill()
        raise e

    return {
        "stdout": stdout.decode(),
        "stderr": stderr.decode(),
        "status": ddsls_process.returncode
    }

# Tests

def test_ddsls_empty():
    data = run_ddsls(["--json", "-t", "dcpspublication"])

    assert data["status"] == 0
    assert data["stdout"] == ""


def test_participant_reported():
    ddsls = start_ddsls_watchmode(["-t", "dcpsparticipant"])

    dp = DomainParticipant(0)

    time.sleep(0.5)

    data = stop_ddsls_watchmode(ddsls)

    assert str(dp.guid) in data["stdout"]
