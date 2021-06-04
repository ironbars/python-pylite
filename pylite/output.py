import sys
import json
from collections import OrderedDict

from tabulate import tabulate


OUTPUT_MODES = dict()


def output_mode(mode):
    def wrapper(func):
        OUTPUT_MODES[mode] = func

        return func
    return wrapper


@output_mode("default")
def _write_default(rows, writer):
    headers = rows[0]
    data = rows[1:]

    print(tabulate(data, headers=headers, tablefmt="grid"), file=writer.dest)


@output_mode("list")
def _write_list(rows, writer):
    data = rows[1:]
    str_data = []
    
    for row in data:
        str_data.append(writer.colsep.join(map(str, row)))

    print(writer.rowsep.join(str_data), file=writer.dest)


@output_mode("line")
def _write_lines(rows, writer):
    fields = rows[0]
    dict_data = rows_to_dict(rows)
    line_data = []
    justify = max(len(field) for field in fields)

    for row in dict_data:
        lines = [
            " ".join([f"{k:>{justify}}", "=", f"{v}"]) 
            for k, v in row.items()
        ]
        row_as_lines = "\n".join(lines)

        line_data.append(row_as_lines)

    print("\n\n".join(line_data), file=writer.dest)
    

@output_mode("json")
def _write_json(rows, writer):
    dict_data = rows_to_dict(rows)

    print(
        "[" + ",\n".join(json.dumps(row) for row in dict_data) + "]",
        file=writer.dest
    )


@output_mode("json-pretty")
def _write_json_pretty(rows, writer):
    dict_data = rows_to_dict(rows)

    print(json.dumps(dict_data, indent=2), file=writer.dest)


@output_mode("python")
def _write_python_list(rows, writer):
    data = rows[1:]

    for row in data:
        print(row, file=writer.dest)


# This is here so that all commands can have a common interface for printing 
# data, which in turn ensures that all output goes to the same place (be it 
# a file or stdout).
@output_mode("meta")
def _write_meta(rows, writer):
    print(rows, file=writer.dest)


class PyliteSqlResultWriterError(Exception):
    pass


class PyliteSqlResultWriter(object):
    def __init__(
        self, 
        mode="default", 
        dest="stdout",
        colsep="|", 
        rowsep="\n"
    ):
        self.mode = mode
        self.dest = dest
        self.colsep = colsep
        self.rowsep = rowsep


    def write_result(self, data, mode=None):
        if mode is not None:
            output_mode = mode
        else:
            output_mode = self.mode

        if output_mode == "meta":
            OUTPUT_MODES[output_mode](data, self)
        else:
            rows = data.fetchall()

            if len(rows) > 0:
                fields = tuple(col[0] for col in data.description)
                rows = [fields] + rows

                OUTPUT_MODES[output_mode](rows, self)

        
    @property
    def mode(self):
        return self._mode


    @mode.setter
    def mode(self, new_mode):
        valid_modes = list(OUTPUT_MODES.keys())
        
        valid_modes.remove("meta")

        if new_mode not in valid_modes:
            raise PyliteSqlResultWriterError("Invalid output mode")

        self._mode = new_mode


    @mode.deleter
    def mode(self):
        self._mode = "default"


    @property
    def dest(self):
        return self._dest


    @dest.setter
    def dest(self, new_dest):
        if new_dest == "stdout":
            self._dest = sys.stdout
        else:
            if not self._dest.closed and self._dest is not sys.stdout:
                self._dest.close()

            self._dest = open(new_dest, "w")


    @dest.deleter
    def dest(self):
        if self._dest is sys.stdout:
            return

        if not self._dest.closed:
            self._dest.close()

        self._dest = sys.stdout


def rows_to_dict(rows):
    fields = rows[0]
    data = rows[1:]
    dict_data = []

    for row in data:
        dict_data.append(OrderedDict(zip(fields, row)))

    return dict_data

