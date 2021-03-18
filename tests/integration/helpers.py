import subprocess

import pytest


def xfailproc(*args):
    return pytest.param(
        *args, marks=pytest.mark.xfail(raises=subprocess.CalledProcessError)
    )
