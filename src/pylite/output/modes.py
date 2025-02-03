from __future__ import annotations

import json
from typing import TYPE_CHECKING, Callable, TypeVar

from tabulate import tabulate

if TYPE_CHECKING:
    from pylite.output import SQLResultWriter


OUTPUT_MODES = dict()
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


@output_mode("markdown")
def _write_markdown(rows: list[tuple[str, ...]], writer: SQLResultWriter) -> None:
    headers = rows[0]
    data = rows[1:]

    print(tabulate(data, headers=headers, tablefmt="github"), file=writer.dest)


@output_mode("html")
def _write_html(rows: list[tuple[str, ...]], writer: SQLResultWriter) -> None:
    headers = rows[0]
    data = rows[1:]

    print(tabulate(data, headers=headers, tablefmt="html"), file=writer.dest)


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
