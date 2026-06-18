from collections import Counter
import os
from pathlib import Path
from typing import Dict, Iterable, Union

import pytest

from organize.output import SavingOutput

# define types for the make_files structure
## just the raw contents of a file
FileContentsRaw = Union[str, bytes]
## file contents plus a timestamp
FileContentsTimeStamp = tuple["FileContentsRaw", float]
## when passing or returning files, use just the data, or can add timestamps
FileContents = Union[FileContentsRaw, FileContentsTimeStamp]
## A FileSpec is a dictionary of:
##   - a file name plus the FileContents
##   - OR a directory name, and a FileSpec that specifies files and subdirs
FileSpec = Dict[str, Union[FileContents, "FileSpec"]]


ORGANIZE_DIR = Path(__file__).parent.parent


@pytest.fixture()
def testoutput() -> SavingOutput:
    return SavingOutput()


def equal_items(a: Iterable, b: Iterable) -> bool:
    return Counter(a) == Counter(b)


def make_files(structure: Union[FileSpec, list[str]], path: Union[Path, str] = "."):
    """Example structure:

    {
        "folder": {
            "subfolder": {
                "test.txt": "",
                "other.pdf": b"binary",
            },
        },
        "file.txt": "Hello world\nAnother line",
    }

    Or, with timestamps, where the timstamps are POSIX file timestamps (see
    os.utime); it is technically possible to only specify timestamps for some
    files and no timestamp for others, but the `read_files*()` function will
    include all timestamps or no timestamps:

    {
        "folder": {
            "subfolder": {
                "empty.txt": ("", 1781818225.400407),
                "other.pdf": ("text", 1781818321.400407),
            },
        },
    }
    """
    if isinstance(path, str):
        path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

    # declare the typing specs
    name: str
    content: Union[FileContents, FileSpec]

    # structure is a list of filenames
    if isinstance(structure, list):
        for name in structure:
            (path / name).touch()
        return

    # structure is a dict
    for name, content in structure.items():
        resource: Path = path / name

        timestamp: Union[float, None] = None

        if isinstance(content, tuple):
            content, timestamp = content

        # folders are dicts
        if isinstance(content, dict):
            make_files(structure=content, path=resource)

        # everything else is a file
        elif content is None:
            resource.touch()
        elif isinstance(content, bytes):
            resource.write_bytes(content)
        elif isinstance(content, str):
            resource.write_text(content)
        else:
            raise ValueError(f"Unknown file data {content}")

        # if a timestamp was provided, set st_atime and st_mtime; we only care
        # about st_mtime, but utime requires both values
        if timestamp is not None:
            os.utime(resource, (timestamp, timestamp))


def read_files(path: Union[Path, str] = ".", with_timestamp: bool = False):
    if isinstance(path, str):
        path = Path(path)

    result: FileSpec = dict()
    for x in path.glob("*"):
        if x.is_file():
            if with_timestamp:
                # timestamp requested, so include it in the results
                result[x.name] = (x.read_text(), x.stat().st_mtime)
            else:
                result[x.name] = x.read_text()
        if x.is_dir():
            result[x.name] = read_files(x, with_timestamp)
    return result
