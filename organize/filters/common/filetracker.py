from pathlib import Path

from pydantic.config import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra='allow', arbitrary_types_allowed=True))
class FileTracker:
    _ignore_symlinks: bool = False

    @classmethod
    def ignore_symlinks(cls, *args, **kwargs):
        self = cls(*args, **kwargs)
        self._ignore_symlinks = True
        return self


    def __post_init__(self):
        self._seen_files: set[Path] = set()

    def track(self, file: Path) -> bool:
        if file in self._seen_files:
            return False
        if self._ignore_symlinks and file.is_symlink():
            return False
        self._seen_files.add(file)
        return True
