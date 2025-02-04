import sys
from io import TextIOWrapper
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
        # Temporary defaults for internal attributes
        self._dest: TextIO = sys.stdout
        self._dest_name: str = dest  # track this as a string
        self._mode = "default"

        # Use the setter logic in case they're initialized to non-default values
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
        original_dest = self._dest

        try:
            self._dest = sys.stderr
            self.write_result(message, mode="meta")
        finally:
            self._dest = original_dest

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, new_mode: str) -> None:
        valid_modes = get_valid_output_modes()

        if new_mode not in valid_modes:
            raise SQLResultWriterError(f"Invalid output mode: {new_mode}")

        # The 'csv' and 'tsv' modes will rely on the stdlib's csv package.  The docs say
        # that, if writing to a file, `newline` should be set to "" to avoid problems.
        # We can use the reconfigure() method to make that change without closing and
        # re-opening the file.
        # Further, if the mode is already 'csv' or 'tsv', we can assume that the change
        # has already been made and no further action is necessary.
        if new_mode in ("csv", "tsv") and self._mode not in ("csv", "tsv"):
            if self._dest_name not in ("stdout", "stderr"):
                if isinstance(self._dest, TextIOWrapper):  # to appease mypy
                    self._dest.reconfigure(newline="")

        # If 'csv' or 'tsv' is not being set as the new mode AND the current mode is one
        # of those, we need to set the file back to normal behavior.
        if new_mode not in ("csv", "tsv") and self._mode in ("csv", "tsv"):
            if self._dest_name not in ("stdout", "stderr"):
                if isinstance(self._dest, TextIOWrapper):  # to appease mypy
                    self._dest.reconfigure(newline=None)

        self._mode = new_mode

    @mode.deleter
    def mode(self) -> None:
        self._mode = "default"

    @property
    def dest(self) -> TextIO:
        if self._dest.closed:
            self._dest = sys.stdout
        return self._dest

    @dest.setter
    def dest(self, new_dest: str) -> None:
        self._ensure_dest_closed()

        if new_dest in ("stdout", "stderr"):
            self._dest = getattr(sys, new_dest)
        else:
            try:
                self._dest = open(new_dest, "w")
            except OSError as e:
                raise SQLResultWriterError(f"Failed to open file {new_dest}: {e}")

        self._dest_name = new_dest

    @dest.deleter
    def dest(self) -> None:
        self._ensure_dest_closed()

        self._dest = sys.stdout
        self._dest_name = "stdout"

    @property
    def dest_name(self) -> str:
        return self._dest_name

    def _ensure_dest_closed(self) -> None:
        if self._dest not in (sys.stdout, sys.stderr) and not self._dest.closed:
            self._dest.close()
