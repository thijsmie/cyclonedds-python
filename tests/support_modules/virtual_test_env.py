import os
import sys
import shutil
import subprocess
from tempfile import TemporaryDirectory
from venv import EnvBuilder

from fuzzy_idl_definition import random_idl_types
import cyclonedds


class VirtualEnvWithPyCCompat:
    def __init__(self):
        self.dir = TemporaryDirectory()
        self.venv = EnvBuilder(
            system_site_packages=True,
            clear=False,
            symlinks=True,
            upgrade=False,
            with_pip=True,
            prompt="",
            upgrade_deps=False
        )
        self.venv.create(self.dir.name)

        dir = os.path.abspath(os.path.join(os.path.dirname(cyclonedds.__file__), ".libs"))
        libs = [f for f in os.listdir(dir) if "idl" in f]

        process = self.run(
            [
                self.executable(), "-m", "pip", "install", "--upgrade", "pip",
            ],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL
        )
        process.communicate()
        assert process.returncode == 0

        pycompatpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "py_c_compat"))

        if os.path.exists(os.path.join(pycompatpath, "_skbuild")):
            shutil.rmtree(os.path.join(pycompatpath, "_skbuild"))
        if os.path.exists(os.path.join(pycompatpath, "cyclonedds_tests_c_compat.egg-info")):
            shutil.rmtree(os.path.join(pycompatpath, "cyclonedds_tests_c_compat.egg-info"))

        fuzzpath = os.path.join(self.dir.name, "test.idl")
        idl, self.typenames = random_idl_types(module="fuzzymod", number=50)
        with open(fuzzpath, "w") as f:
            f.write(idl)

        process = self.run(
            [
                self.executable(), "-m", "pip", "install", "-q", "--use-feature=in-tree-build",
                pycompatpath
            ],
            env={
                "FUZZY_LOCATION": fuzzpath,
                "FUZZY_MODULE": "fuzzymod",
                "FUZZY_TYPES": ";".join(self.typenames),
                "IDLPY": os.path.join(dir, libs[0])
            }
        )
        process.communicate()
        assert process.returncode == 0

    def executable(self):
        if sys.platform == "win32":
            return os.path.join(self.dir.name, "Scripts", "python.exe")
        return os.path.join(self.dir.name, "bin", "python")

    def environment(self):
        base = os.environ.copy()
        base.update({
            "PATH": os.pathsep.join([os.path.dirname(self.executable())] + base.get("PATH", "").split(os.pathsep)),
            "VIRTUAL_ENV": self.dir.name
        })

        if "PYTHONPATH" in base:
            del base["PYTHONPATH"]

        if "CYCLONEDDS_HOME" in base:
            base["CMAKE_PREFIX_PATH"] = os.pathsep.join(
                [base["CYCLONEDDS_HOME"]] + base.get("CMAKE_PREFIX_PATH", "").split(os.pathsep)
            )
            base["LD_LIBRARY_PATH"] = os.pathsep.join(
                [base["CYCLONEDDS_HOME"] + "/lib", base["CYCLONEDDS_HOME"] + "/lib64"] + base.get("LD_LIBRARY_PATH", "").split(os.pathsep)
            )
            base["DYLD_LIBRARY_PATH"] = os.pathsep.join(
                [base["CYCLONEDDS_HOME"] + "/lib"] + base.get("DYLD_LIBRARY_PATH", "").split(os.pathsep)
            )

        return base

    def run(self, args, **kwargs):
        if "env" in kwargs:
            env = self.environment()
            env.update(kwargs["env"])
            kwargs["env"] = env
        else:
            kwargs["env"] = self.environment()
        return subprocess.Popen(args, **kwargs)

    def __del__(self):
        self.dir.cleanup()

