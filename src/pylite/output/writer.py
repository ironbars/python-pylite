import sys
from sqlite3 import Cursor
from typing import TextIO

from pylite.exceptions import SQLResultWriterError
from pylite.output.modes import OUTPUT_MODES, get_valid_output_modes


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
        self.colsep: str = colsep
        self.rowsep: str = rowsep

    def write_result(self, data: str | Cursor, mode: str | None = None) -> None:
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

    def write_error(self, message: str) -> None:
        original_dest = self.dest

        try:
            self.dest = "stderr"  # type: ignore[assignment]
            self.write_result(message, mode="meta")
        finally:
            # Here, we need to assign to the underlying TextIO object since:
            # 1. That is what's returned by self.dest, thus is what original_dest holds
            # 2. We don't have access to the string used to create original_dest
            self._dest = original_dest

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
        elif new_dest == "stderr":
            self._dest = sys.stderr
        else:
            try:
                self._dest = open(new_dest, "w")
            except OSError as e:
                raise SQLResultWriterError(f"Failed to open file {new_dest}: {e}")

    @dest.deleter
    def dest(self) -> None:
        self._ensure_dest_closed()

        self._dest = sys.stdout

    def _ensure_dest_closed(self) -> None:
        if self._dest not in (sys.stdout, sys.stderr) and not self._dest.closed:
            self._dest.close()
