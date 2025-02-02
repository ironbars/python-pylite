import argparse
import sys
from typing import Never

from pylite.exceptions import REPLResetEvent
from pylite.session import PylitePromptSession


class DotCommandArgParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        self.print_usage(sys.stderr)
        raise REPLResetEvent


class DotCommand:
    def __init__(self, name: str) -> None:
        self.name = name
        self.parser = self.get_parser()

    def execute(self, cmd_args: list[str], session: PylitePromptSession) -> None:
        raise NotImplementedError

    def get_parser(self) -> DotCommandArgParser:
        raise NotImplementedError
