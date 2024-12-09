"""Version-related utilities."""

import re
import sys
from functools import cache
from pathlib import Path

from rich import print  # noqa:A004

from .retval import EX_SOFTWARE


@cache
def get_version() -> str:
    """Get current Bonaparte version."""

    def is_semantic_version_number(version: str) -> bool:
        """Check if the version number respects the “semantic versioning” pattern."""
        return re.match(r"^(?:0|[1-9]\d*)"
                        r"[.](?:0|[1-9]\d*)"
                        r"[.](?:0|[1-9]\d*)"
                        r"(?:-(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:[.](?:0|[1-9]\d*|\d*[a-zA-Z-]["
                        r"0-9a-zA-Z-]*))*)?"
                        r"(?:[+][0-9a-zA-Z-]+(?:[.][0-9a-zA-Z-]+)*)?$", version) is not None

    try:
        _version = (Path(__file__).parent.parent / "version").read_text().strip()
        if is_semantic_version_number(_version):
            return _version
        print(f"[bold red]:x:  version isn’t a valid semver ({_version})", file=sys.stderr, flush=True)
        sys.exit(EX_SOFTWARE)
    except FileNotFoundError as ex:
        print(f"[bold red]:x:  Can’t find the 'version' file: {ex.filename}", file=sys.stderr, flush=True)
        sys.exit(EX_SOFTWARE)
    except PermissionError as ex:
        print(f"[bold red]:x:  Can’t read the 'version' file: {ex}", file=sys.stderr, flush=True)
        sys.exit(EX_SOFTWARE)
