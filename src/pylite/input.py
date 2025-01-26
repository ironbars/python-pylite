from collections.abc import Iterator
from pathlib import Path
from sqlite3 import complete_statement
from typing import Any, Optional

from prompt_toolkit import PromptSession

from pylite.exceptions import SQLReaderError

DEFAULT_PROMPT_MESSAGE = "pylite> "
DEFAULT_PROMPT_CONTINUATION = "   ...> "


class SQLReader:
    def __init__(self, source: Optional[Any] = None) -> None:
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


class SQLFileReader(SQLReader):
    def __init__(self, source: str | Path) -> None:
        path = Path(source)

        if not path.exists():
            raise SQLReaderError(f"File '{source}' doesn't exist or is not readable")

        super().__init__(source)

    def __iter__(self):
        with open(self.source, "r") as sf:
            sql_gen = (line.split("--")[0].strip() for line in sf)

            for line in sql_gen:
                yield self.build_complete_statement(line, sql_gen)

    def get_next(self, sql_src: Iterator[str]) -> str:
        return next(sql_src)


class SQLPromptReader(SQLReader):
    def __init__(
        self,
        source: Optional[PromptSession],
        message: str = DEFAULT_PROMPT_MESSAGE,
        continuation: str = DEFAULT_PROMPT_CONTINUATION,
    ) -> None:
        if source is None:
            raise SQLReaderError("'source' cannot be None for SQLPromptReader")

        self.message = message
        self.continuation = continuation

        super().__init__(source)

    def prompt(self) -> str:
        assert self.source is not None  # to appease mypy

        text = self.source.prompt(self.message)

        if text.startswith("."):
            return text

        return self.build_complete_statement(text, self.source)

    def get_next(self, sql_src: PromptSession) -> str:
        return sql_src.prompt(self.continuation)
