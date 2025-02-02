from pathlib import Path
from typing import Iterator

from pylite.exceptions import SQLReaderError
from pylite.input.reader import SQLReader


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
