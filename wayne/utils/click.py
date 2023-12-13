# coding=utf-8

""" Click-related utilities. """

from pathlib import Path

import click
from click import Argument, Context


class OutputFile(click.Path):
    """ Parameter is an output file. """
    name = "output_file"
    """ Parameter’s name. """

    def __init__(self, suffix: str | None = None, exist_ok: bool = False) -> None:
        super().__init__(dir_okay=False)
        self.suffix = suffix
        """ Suffix to validate. """
        self.exist_ok = exist_ok
        """ Is it acceptable that the folder already exists? """

    def convert(self, value: str, param: Argument | None, ctx: Context | None) -> Path:
        """ Convert the input to a resolved and expanded path. """
        path = Path(value).expanduser().resolve()

        path = Path(super().convert(path, param, ctx))

        if path.exists() and not self.exist_ok:
            self.fail(f"Path {path} already exists.", param, ctx)

        if self.suffix and self.suffix != path.suffix:
            self.fail(f"File {path} as wrong suffix ({self.suffix}).", param, ctx)

        return path
