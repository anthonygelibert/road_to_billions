# coding=utf-8

""" Typed configuration. """

import sys
from functools import cache
from utils.retval import EX_CONFIG
from pathlib import Path
from typing import Annotated, TypeAlias

from pydantic import AfterValidator, BaseModel, ValidationError


def check_set_settings(val: str) -> str:
    """ Ensure that `val` isn’t “CHANGE_ME.” """
    if val == "CHANGE_ME":
        raise ValueError("Please, change the default value…")
    return val


SetString: TypeAlias = Annotated[str, AfterValidator(check_set_settings)]


class Settings(BaseModel, frozen=True):
    """ Bonaparte settings. """
    api_key: SetString
    api_secret: SetString


@cache
def get_config() -> Settings:
    """ Current configuration. """
    try:
        return Settings.model_validate_json((Path(__file__).parent.parent / "config.json").read_text())
    except FileNotFoundError as ex:
        print(f"[bold red]:x:  Can't find the 'config.json' file: {ex.filename}", file=sys.stderr, flush=True)
        sys.exit(EX_CONFIG)
    except ValidationError as ex:
        print(f"[bold red]:x:  'config.json' is not a valid config JSON file: {ex}", file=sys.stderr, flush=True)
        sys.exit(EX_CONFIG)
