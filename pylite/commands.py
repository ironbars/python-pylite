import shlex

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

            session.write_result(result)
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

    session.write_result(result.fetchone()[0] + ";", mode="meta")
    
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
        session.write_result(row[0], mode="meta")

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
        session.continuation = new_continuation
    else:
        del session.continuation

    raise KeyboardInterrupt


@cmd(".mode")
def _mode(cmd_args, session):
    mode = cmd_args[0] if len(cmd_args) > 0 else "default"
    session.mode = mode

    raise KeyboardInterrupt


@cmd(".output")
def _output(cmd_args, session):
    out = cmd_args[0] if len(cmd_args) > 0 else "stdout"
    session.dest = out

    raise KeyboardInterrupt


@cmd(".dump")
def _dump(cmd_args, session):
    table = cmd_args[0] if len(cmd_args) > 0 else None
    connection = session.connection

    if table is not None:
        dump = ["BEGIN TRANSACTION;"]
        sql = "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?"
        schema = connection.execute(sql, (table,)).fetchone()

        if not schema:
            print("Table {} not found".format(table))
            raise KeyboardInterrupt
        
        dump.append(schema[0] + ";")

        tbl_info = connection.execute(
            "SELECT * FROM pragma_table_info(?)", (table,)
        )
        column_names = [str(row[1]) for row in tbl_info.fetchall()]
        insert_statements_sql = (
            "SELECT 'INSERT INTO {} VALUES(" +
            ",".join(["'||quote(" + col + ")||'" for col in column_names]) +
            ");' FROM {}"
        ).format(table, table)
        insert_statements = connection.execute(insert_statements_sql)

        dump.extend([s[0] for s in insert_statements.fetchall()])
        dump.append("COMMIT;")
        session.write_result("\n".join(dump), mode="meta")
    else:
        for line in session.connection.iterdump():
            session.write_result(line, mode="meta")
        
    raise KeyboardInterrupt
