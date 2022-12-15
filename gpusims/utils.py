import sys
import stat
import shutil
import os
import shlex
from timeit import default_timer as timer
import re
import unicodedata
import subprocess as sp
from pathlib import Path


class ExecError(Exception):
    def __init__(self, cmd, status, stdout, stderr):
        self.cmd = cmd
        self.status = status
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(
            "command completed with non-zero exit code ({})".format(status)
        )


def run_cmd(cmd, cwd=None, shell=False, timeout_sec=None, env=None):
    if not shell and not isinstance(cmd, list):
        cmd = shlex.split(cmd)
    print("running", cmd)
    if isinstance(cmd, list):
        print("running", " ".join(cmd))

    if isinstance(cwd, Path):
        cwd = str(cwd.absolute())

    # the subprocess may take a long time, hence flush all buffers before
    sys.stdout.flush()
    start = timer()
    proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, cwd=cwd, env=env, shell=shell)
    try:
        stdout, stderr = proc.communicate(timeout=timeout_sec)
    except sp.TimeoutExpired as timeout:
        raise timeout

    stdout = stdout.decode("utf-8")
    stderr = stderr.decode("utf-8")
    if proc.returncode != 0:
        print("\nstdout (last 15 lines):\n")
        print("\n".join(stdout.splitlines()[-15:]))
        print("\nstderr (last 15 lines):\n")
        print("\n".join(stderr.splitlines()[-15:]))
        # there may be a loooot to print, block!
        sys.stdout.flush()
        raise ExecError(cmd=cmd, status=proc.returncode, stdout=stdout, stderr=stderr)

    end = timer()
    duration = end - start
    return proc.returncode, stdout, stderr, duration


def ensure_empty(d):
    try:
        print("removing", str(d.absolute()))
        shutil.rmtree(str(d.absolute()))
    except FileNotFoundError:
        pass
    # also creates parents
    os.makedirs(str(d.absolute()), exist_ok=True)


def chmod_x(executable):
    executable.chmod(executable.stat().st_mode | stat.S_IEXEC)


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def merge_dicts(*dicts):
    merged = {}
    for d in dicts:
        merged.update(d)
    return merged


def dedup_stable(seq):
    seen = set()
    return [x for x in seq if not (x in seen or seen.add(x))]


def add_paths_to_env(env, paths):
    new_paths = os.environ.get(env, "").split(os.pathsep)
    new_paths += [str(p) for p in paths]
    # filter empty paths
    new_paths = [p for p in new_paths if len(p) > 0]
    new_paths = os.pathsep.join(dedup_stable(new_paths))
    os.environ[env] = new_paths
    print("{}={}".format(env, new_paths))
    return new_paths
