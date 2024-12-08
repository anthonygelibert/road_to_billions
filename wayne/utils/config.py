"""Typed configuration."""

import sys
from functools import cache
from pathlib import Path
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, ValidationError

from utils.retval import EX_CONFIG


def check_set_settings(val: str) -> str:
    """
    Check “val” isn’t CHANGE_ME.

    :raise ValueError: Value is still the default one.
    """
    if val == "CHANGE_ME":
        msg = "Please, change the default value…"
        raise ValueError(msg)
    return val


type SetString = Annotated[str, AfterValidator(check_set_settings)]


class Settings(BaseModel):
    """Bonaparte settings."""

    model_config = ConfigDict(frozen=True)

    api_key: SetString
    api_secret: SetString


@cache
def get_config() -> Settings:
    """Get the current configuration."""
    try:
        return Settings.model_validate_json((Path(__file__).parent.parent / "config.json").read_text())
    except FileNotFoundError as ex:
        print(f"[bold red]:x:  Can't find the 'config.json' file: {ex.filename}", file=sys.stderr, flush=True)
        sys.exit(EX_CONFIG)
    except ValidationError as ex:
        print(f"[bold red]:x:  'config.json' is not a valid config JSON file: {ex}", file=sys.stderr, flush=True)
        sys.exit(EX_CONFIG)
