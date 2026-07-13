from pathlib import Path
from typing import Generator, List, Optional, Tuple, Union


import pytest
from arrow import Arrow
from arrow import get as arrow_get
from pydantic_core import ValidationError
from pyfakefs.fake_filesystem import FakeFilesystem, FakeFile

from organize.filters.skip import Skip
from organize.output import Default as Output
from organize.resource import Resource

from pydantic import BaseModel, ConfigDict


class FFS(BaseModel):
    fs: FakeFilesystem

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def create_file(
        self,
        file: str,
        mtime: Optional[Arrow] = None,
        ctime: Optional[Arrow] = None,
    ) -> FakeFile:
        fake_file = self.fs.create_file(file)
        if mtime:
            fake_file.st_mtime = mtime.timestamp()
        if ctime:
            fake_file.st_ctime = ctime.timestamp()
        return fake_file

    def create_path(self, *args, **kwargs) -> Path:
        return Path((self.create_file(*args, **kwargs)).name)


@pytest.fixture
def ffs(fs: FakeFilesystem):
    return FFS(fs=fs)


def test_tracks_seen_files(ffs):
    ## arrange
    skipper = Skip()
    f = ffs.create_path("/a")

    ## act
    process = skipper.pipeline(Resource(f), Output())

    ## assert
    # with only one file, we should skip it
    assert process is False
    # we should track that we have seen the file
    assert f in skipper._seen_files


def test_ignores_symlinks(ffs):
    ## arrange
    skipper = Skip()
    f = ffs.create_path("/a")
    s = Path("/a_link")
    s.symlink_to(f)

    ## act
    process = skipper.pipeline(Resource(s), Output())

    ## assert
    # should not process symlink files
    assert process is False
    # should not track symlink files
    assert s not in skipper._seen_files


@pytest.fixture
def files_with_relative_ts(
    ffs, offsets: List[int], order: Optional[List[int]]
) -> Generator[List[Path], None, None]:
    """fixture to create several files with timestamps

    Parameters:
    - `offsets`: an array of offsets in seconds for the modified timestamp;
      the value of the offset is added to the time when the function is called
    - `order`: (optional) the order to create the files in; by default, they
      will be created in the natural order provided by the offsets; the value of
      order will be used as the index into the `offsets` list

    Example explaining `offsets` and `order`:
    - `offsets = [2, 0, 1]`
    - `order = None`:
    - Three files will be created:
      - index 0: `/file_0` will be created with its mtime with 2 seconds
        (from `offsets[0] = 2`)
      - index 1: `/file_1`, mtime is +0 (`offsets[1] = 0`)
      - index 2: `/file_2`, mtime is +1 (`offsets[2] = 1`)

    Example 2:
    - `offsets = [5, 5, 5]`
    - `order = [2, 0, 1]`
    - Three files will be created, in the following order:
      - order[0] -> 2 -> offsets[2]: `/file_2`, mtime is +5
      - order[1] -> 0 -> offsets[0]: `/file_0`, mtime is +5
      - order[2] -> 1 -> offsets[1]: `/file_1`, mtime is +5
    """
    ctime: Optional[Arrow] = None
    now = Arrow(2026, 7, 12, 15)
    paths: List[Path] = list()
    for i in range(len(offsets)):
        mtime = now.shift(seconds=offsets[i])
        if order:
            ctime = now.shift(seconds=order[i])
        paths.append(ffs.create_path(f"/file_{i}", mtime, ctime))
    yield paths


FilterResponse = tuple[bool, Path]



def check_skips(files, count, acted, kept):
    ## arrange
    skipper = Skip(count=count)
    processed: list[FilterResponse] = list()

    ## act
    for p in files:
        res = Resource(p)
        process: bool = skipper.pipeline(res, Output())
        assert res.path is not None
        response = FilterResponse((process, res.path))
        processed.append(response)

    ## assert
    assert skipper._skipped == kept

    # check responses for each file
    for i, act in enumerate(acted):
        process, path = processed[i]
        if act is None:
            assert process is False
        else:
            assert path == files[act]

@pytest.mark.parametrize(
    ["offsets", "order", "count", "seen", "acted"],
    [
        ([0, 1, 2], None, 1, None, [None, 1, 2]),
        ([0, 1, 2, 3], None, 2, None, [None, None, 2, 3]),
        ([0, 1, 2, 3], None, 3, None, [None, None, None, 3]),
        ([0, 1, 2, 3], None, 1, [3,2,1,0], [None, 3, 2, 1]),
    ],
)
def test_skips_by_name(files_with_relative_ts, count, seen, acted):
    paths: list[Path]
    kept: list[Path]
    if seen is None:
        paths = files_with_relative_ts.copy()
        kept = paths[:count]
    else:
        paths = list()
        kept = list()
        for i in seen:
            file = files_with_relative_ts[i]
            paths.append(file)
            if i not in acted:
                kept.append(file)

    check_skips(paths, count, acted, kept)
