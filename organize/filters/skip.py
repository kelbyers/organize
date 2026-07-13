from pathlib import Path
from typing import Any, Callable, ClassVar, Literal, NamedTuple, Tuple, Optional

from pydantic.config import ConfigDict
from pydantic.dataclasses import dataclass

from organize.filter import FilterConfig
from organize.output import Output
from organize.resource import Resource

from organize.filters.common.filetracker import FileTracker


def detect_skipped(
    skipped: list[Path],
    count: int,
    unknown: Path,
) -> tuple[list[Path], Optional[Path]]:
    keepers = skipped[:]
    unskipped = None
    keepers.append(unknown)
    if len(keepers) > count:
        unskipped = keepers.pop()
    return keepers, unskipped


# @dataclass(config=ConfigDict(extra="forbid"))
class Skip(FileTracker):
    """skip junk"""

    count: int = 1

    filter_config: ClassVar[FilterConfig] = FilterConfig(
        name="skip", files=True, dirs=True
    )

    # model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    def __post_init__(self):
        super().__post_init__()
        self._ignore_symlinks = True

        self._skipped: list[Path] = list()

        assert isinstance(self.count, int)

    def pipeline(self, res: Resource, output: Output) -> bool:
        assert res.path is not None, "Does not support standalone mode"

        if not self.track(res.path):
            return False

        skipped, unskipped = detect_skipped(self._skipped, self.count, res.path)
        self._skipped = skipped
        if unskipped:
            res.path = unskipped
            return True

        return False
