import shlex

from .output import print_result
from .input import PyliteSqlFileReader, PyliteSqlReaderError

COMMANDS = dict()


def handle_dot_command(text, session):
    tokens = shlex.split(text)
    command = tokens[0]
    cmd_args = tokens[1:]

    try:
        COMMANDS[command](cmd_args, session)
    except KeyError:
        print("Unrecognized command: {}".format(command))


def cmd(name):
    def wrapper(func):
        COMMANDS[name] = func

        return func
    return wrapper


# All commands need to raise either EOFError to exit, or KeyboardInterrupt to
# continue the main REPL

@cmd(".quit")
def _quit(cmd_args, session):
    raise EOFError


@cmd(".read")
def _read(cmd_args, session):
    sql_file = cmd_args[0]
    reader = PyliteSqlFileReader(sql_file)

    try:
        for sql in reader:
            result = session.connection.execute(sql)

            print_result(result)
    except PyliteSqlReaderError:
        print("Incomplete statement")

    raise KeyboardInterrupt


@cmd(".schema")
def _schema(cmd_args, session):
    sql = "SELECT sql FROM sqlite_master WHERE type = 'table'"
    table = cmd_args[0] if len(cmd_args) > 0 else None

    if table is not None:
        sql += " AND name = ?"
        result = session.connection.execute(sql, (table,))
    else:
        result = session.connection.execute(sql)

    print(result.fetchone()[0] + ";")
    
    raise KeyboardInterrupt


@cmd(".tables")
def _tables(cmd_args, session):
    sql = "SELECT name FROM sqlite_master WHERE type = 'table'"
    table = cmd_args[0] if len(cmd_args) > 0 else None

    if table is not None:
        sql += " AND name LIKE ?"
        result = session.connection.execute(sql, (table,))
    else:
        result = session.connection.execute(sql)

    for row in result.fetchall():
        print(row[0])

    raise KeyboardInterrupt


@cmd(".prompt")
def _prompt(cmd_args, session):
    new_message = cmd_args[0] if len(cmd_args) > 0 else None
    new_continuation = cmd_args[1] if len(cmd_args) > 1 else None

    if new_message is not None:
        session.message = new_message
    else:
        del session.message

    if new_continuation is not None:
        session.reader.continuation = new_continuation
    else:
        del session.continuation

    raise KeyboardInterrupt

