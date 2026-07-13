from organize.filters.common.filetracker import FileTracker
import pytest
from pydantic import BaseModel, ConfigDict
from pyfakefs.fake_filesystem import FakeFile, FakeFilesystem
from typing import Optional
from arrow import Arrow
from pathlib import Path

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
    
    @classmethod
    def create_symlink(cls, existing: Path, link: str) -> Path:
        path = Path(link)
        path.symlink_to(existing)
        return path

@pytest.fixture
def ffs(fs: FakeFilesystem):
    return FFS(fs=fs)

def test_tracks_seen_files(ffs):
    ## arrange
    p = ffs.create_path("/a")
    ft = FileTracker()

    ## act
    tracked = ft.track(p)

    ## assert
    assert tracked is True
    assert p in ft._seen_files

def test_only_sees_files_once(ffs):
    ## arrange
    p = ffs.create_path("/a")
    ft = FileTracker()

    ## act
    tracked = ft.track(p)
    second = ft.track(p)

    ## assert
    assert p in ft._seen_files
    assert tracked is True
    assert second is False

def test_can_track_symlinks(ffs):
    ## arrange
    p = ffs.create_path("/a")
    ft = FileTracker()
    s = ffs.create_symlink(p, "/s")

    ## act
    tracked = ft.track(s)

    ## assert
    assert s in ft._seen_files
    assert tracked is True
    assert ft._ignore_symlinks is False

def test_can_ignore_symlinks(ffs):
    ## arrange
    p = ffs.create_path("/a")
    ft = FileTracker.ignore_symlinks()
    s = ffs.create_symlink(p, "/s")

    ## act
    tracked = ft.track(s)

    ## assert
    assert ft._ignore_symlinks is True
    assert tracked is False
    assert s not in ft._seen_files
