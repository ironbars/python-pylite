import json
import sys
from sqlite3 import Cursor
from typing import Callable, Optional, TextIO, TypeVar

from tabulate import tabulate

from pylite.exceptions import SQLResultWriterError

OUTPUT_MODES = dict()


class SQLResultWriter:
    def __init__(
        self,
        mode: str = "default",
        dest: str = "stdout",
        colsep: str = "|",
        rowsep: str = "\n",
    ) -> None:
        self._dest: TextIO = sys.stdout
        self.mode = mode
        self.dest = dest  # type: ignore[assignment]
        self.colsep = colsep
        self.rowsep = rowsep

    def write_result(self, data: str | Cursor, mode: Optional[str] = None):
        output_mode = mode or self.mode

        if output_mode == "meta":
            print(data, file=self.dest)
        elif isinstance(data, Cursor):  # to appease mypy
            rows = data.fetchall()

            if len(rows) > 0:
                fields = tuple(col[0] for col in data.description)
                rows = [fields] + rows

                OUTPUT_MODES[output_mode](rows, self)
        else:  # should never get here
            raise TypeError("Invalid data type provided to write_result()")

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, new_mode: str) -> None:
        valid_modes = get_valid_output_modes()

        if new_mode not in valid_modes:
            raise SQLResultWriterError(f"Invalid output mode: {new_mode}")

        self._mode = new_mode

    @mode.deleter
    def mode(self) -> None:
        self._mode = "default"

    @property
    def dest(self) -> TextIO:
        return self._dest

    @dest.setter
    def dest(self, new_dest: str) -> None:
        self._ensure_dest_closed()

        if new_dest == "stdout":
            self._dest = sys.stdout
        else:
            try:
                self._dest = open(new_dest, "w")
            except OSError as e:
                raise SQLResultWriterError(f"Failed to open file {new_dest}: {e}")

    @dest.deleter
    def dest(self) -> None:
        self._ensure_dest_closed()

        self._dest = sys.stdout

    def _ensure_dest_closed(self):
        if self._dest is not sys.stdout and not self._dest.closed:
            self._dest.close()


T = TypeVar("T", bound=Callable)


def output_mode(mode: str) -> Callable[[T], T]:
    def wrapper(func: T) -> T:
        OUTPUT_MODES[mode] = func

        return func

    return wrapper


@output_mode("default")
def _write_default(rows: list[tuple[str, ...]], writer: SQLResultWriter) -> None:
    headers = rows[0]
    data = rows[1:]

    print(tabulate(data, headers=headers, tablefmt="grid"), file=writer.dest)


@output_mode("list")
def _write_list(rows: list[tuple[str, ...]], writer: SQLResultWriter) -> None:
    data = rows[1:]
    str_data = []

    for row in data:
        str_data.append(writer.colsep.join(map(str, row)))

    print(writer.rowsep.join(str_data), file=writer.dest)


@output_mode("line")
def _write_lines(rows: list[tuple[str, ...]], writer: SQLResultWriter) -> None:
    fields = rows[0]
    dict_data = rows_to_dict(rows)
    line_data = []
    justify = max(len(field) for field in fields)

    for row in dict_data:
        lines = [" ".join([f"{k:>{justify}}", "=", f"{v}"]) for k, v in row.items()]
        row_as_lines = "\n".join(lines)

        line_data.append(row_as_lines)

    print("\n\n".join(line_data), file=writer.dest)


@output_mode("json")
def _write_json(rows: list[tuple[str, ...]], writer: SQLResultWriter) -> None:
    dict_data = rows_to_dict(rows)

    print(
        "[" + ",\n".join(json.dumps(row) for row in dict_data) + "]", file=writer.dest
    )


@output_mode("json-pretty")
def _write_json_pretty(rows: list[tuple[str, ...]], writer: SQLResultWriter) -> None:
    dict_data = rows_to_dict(rows)

    print(json.dumps(dict_data, indent=2), file=writer.dest)


@output_mode("python")
def _write_python_list(rows: list[tuple[str, ...]], writer: SQLResultWriter) -> None:
    data = rows[1:]

    for row in data:
        print(row, file=writer.dest)


def rows_to_dict(rows: list[tuple]) -> list[dict[str, str]]:
    fields = rows[0]
    data = rows[1:]
    dict_data = []

    for row in data:
        dict_data.append(dict(zip(fields, row)))

    return dict_data


def get_valid_output_modes() -> list[str]:
    valid = list(OUTPUT_MODES.keys())

    return sorted(valid)
