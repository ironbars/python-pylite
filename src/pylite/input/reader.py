from collections.abc import Iterator
from sqlite3 import complete_statement
from typing import Any

from pylite.exceptions import SQLReaderError


class SQLReader:
    def __init__(self, source: Any | None = None) -> None:
        self.source = source

    def build_complete_statement(self, text: str, sql_src: Iterator[str]) -> str:
        statement_components = [text]

        while not complete_statement(" ".join(statement_components)):
            try:
                statement_components.append(self.get_next(sql_src))
            except StopIteration:
                raise SQLReaderError("Incomplete statement")

        return " ".join(statement_components)

    def get_next(self, sql_src: Any):
        raise NotImplementedError
