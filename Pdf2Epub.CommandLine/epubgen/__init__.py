from typing import Iterator
from dataclasses import dataclass
from contextlib import contextmanager
import os
import shutil
import tempfile
import zipfile


@dataclass
class EpubData:
    title: str
    html: str


@contextmanager
def push_dir(path: str) -> Iterator[None]:
    """A simulation of `pushdir` and `popdir` command."""

    prev_path = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(prev_path)


def duplicate_template() -> str:
    """Make a copy of the template directory."""

    module_dir = os.path.split(__file__)[0]
    template_dir = os.path.join(module_dir, 'template')
    return shutil.copytree(template_dir, tempfile.mktemp())


def create_epub(epub_data: EpubData) -> str:
    """Create an ePub file based on given data and the template."""

    def is_unwanted_file(fname: str) -> bool:
        """Whether a file is unwanted in the generated ePub result."""

        return fname in ['.DS_Store']

    with push_dir(duplicate_template()):
        with open('OEBPS/page-00001.html', 'r') as f:
            html_template = f.read()
        with open('OEBPS/page-00001.html', 'w') as f:
            f.write(html_template.format(
                body=epub_data.html
            ))
        fname = tempfile.mktemp(suffix='.epub')
        with zipfile.ZipFile(fname, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(os.curdir):
                for file in files:
                    if is_unwanted_file(os.path.split(file)[1]):
                        continue
                    zipf.write(os.path.join(root, file))
    return fname
