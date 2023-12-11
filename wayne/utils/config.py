# coding=utf-8

""" Typed configuration. """

import sys
from functools import cache
from os import EX_CONFIG
from pathlib import Path

from pydantic import BaseModel, ValidationError


class Settings(BaseModel, frozen=True):
    """ Bonaparte settings. """
    api_key: str
    api_secret: str


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
