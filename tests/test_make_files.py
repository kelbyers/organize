from datetime import datetime
from pathlib import Path

from conftest import make_files, read_files


def test_make_files(fs):
    files = {
        "folder": {
            "subfolder": {
                "test.txt": "",
                "other.pdf": "text",
            },
        },
        "file.txt": "Hello world\nAnother line",
    }

    make_files(files, "test")
    assert read_files("test") == files


def test_make_files_from_list(fs):
    names = ["asd.txt", "newname 2.pdf", "newname.pdf", "test.pdf"]
    make_files(names, "test")

    for name in names:
        assert (Path("test") / name).exists()


def test_make_files_with_timestamp(fs):
    ts1 = datetime(2020, 1, 1).timestamp()
    ts2 = datetime(2020, 1, 2).timestamp()
    ts3 = datetime(2020, 1, 3).timestamp()

    files = {
        "folder": {
            "subfolder": {
                "test.txt": ("", ts2),
                "other.pdf": ("text", ts3),
            },
        },
        "foo.txt": ("content", ts1),
    }

    make_files(files, "test")
    assert read_files("test", True) == files
