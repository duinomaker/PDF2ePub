from typing import Any, Callable, Iterable, Iterator, TypeVar
from contextlib import contextmanager
import numpy as np
import os
import tempfile
import subprocess
import math

T = TypeVar('T')
U = TypeVar('U')


def curry_first_arg(fn):
    """Perform function currying on the first (positional) argument."""

    return lambda arg: lambda *args, **kwargs: fn(arg, *args, **kwargs)


def split_on(pred, elements):
    """Split an iterable on a predicate."""

    t, f = [], []
    for e in elements:
        (t if pred(e) else f).append(e)
    return t, f


def filter_dict_by(props: list[str], dic: dict[str, Any]) -> dict[str, Any]:
    """Only retains specified properties of a dict."""

    return {p: dic[p] for p in props}


@contextmanager
def push_dir(path: str) -> Iterator[None]:
    """A simulation of `pushdir` and `popdir` command."""

    prev_path = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(prev_path)


def make_file_temp(src: str) -> str:
    """Moves a file to a temporary path."""

    path_dest = tempfile.mkdtemp()
    _, fname = os.path.split(src)
    dest = os.path.join(path_dest, fname)
    os.rename(src, dest)
    return dest


def latex_to_pdf(src: str) -> str:
    """Compiles a LaTeX source file to PDF."""

    path_src, fname = os.path.split(src)
    fname_pdf = os.path.splitext(fname)[0] + '.pdf'
    with push_dir(path_src):
        subprocess.run(['latexmk', '-pdf', fname])
        subprocess.run(['latexmk', '-c', fname])
    path_src_pdf = os.path.join(path_src, fname_pdf)
    path_dest_pdf = make_file_temp(path_src_pdf)
    return path_dest_pdf


def accuracy(base: str, subj: str, stub: str = '\n') -> tuple[int, int, int]:
    """Compares two strings, returns a tuple (x, y, z), where
    x: times there should be a `stub` in `subj` but there is none;
    y: times there should not be a `stub` in `subj` but there is one;
    z: number of presence of `stub` in `base`.

    base and subj should be identical if got rid of all stubs."""

    i, j = 0, 0
    x, y, z = 0, 0, 0
    i_end, j_end = len(base), len(subj)
    while i < i_end and j < j_end:
        if base[i] == stub:
            i += 1
            z += 1
            if subj[j] == stub:
                j += 1
            else:
                x += 1
        elif subj[j] == stub:
            j += 1
            y += 1
        else:
            assert base[i] == subj[j]
            i += 1
            j += 1
    return x, y, z


def is_binary(arr: Iterable[float]) -> bool:
    """Whether the histogram of an array will have two ``peaks''."""

    arr = list(arr)
    mean = sum(arr) / len(arr)
    l, r = split_on(lambda n: n < mean, arr)
    if len(l) < 0.05 * len(arr) or len(r) < 0.05 * len(arr):
        return False
    l, r = np.array(l), np.array(r)
    ml, mr = l.mean(), r.mean()
    vl = math.sqrt(((l - ml) ** 2).mean())
    vr = math.sqrt(((r - mr) ** 2).mean())
    lb = ml + 2.0 * vl
    rb = mr - 2.0 * vr
    return lb < mean < rb
