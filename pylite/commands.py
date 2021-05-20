from .output import print_result
from .reader import PyliteSqlReader, PyliteSqlReaderError

COMMANDS = dict()


def handle_dot_command(text, connection):
    tokens = text.split()
    command = tokens[0]
    cmd_args = tokens[1:]

    try:
        COMMANDS[command](cmd_args, connection)
    except KeyError:
        print("Unrecognized command: {}".format(command))


def cmd(name):
    def wrapper(func):
        COMMANDS[name] = func

        return func
    return wrapper


# All commands need to raise either EOFError to exit, or KeyboardInterrupt to
# continue

@cmd(".quit")
def _quit(cmd_args, connection):
    raise EOFError


@cmd(".read")
def _read(cmd_args, connection):
    sql_file = cmd_args[0]
    reader = PyliteSqlReader(sql_file)

    try:
        for sql in reader:
            result = connection.execute(sql)

            print_result(result)
    except PyliteSqlReaderError:
        print("Incomplete statement")

    raise KeyboardInterrupt
