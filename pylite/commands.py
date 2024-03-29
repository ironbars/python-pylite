import sys
import shlex
import argparse

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText

from .input import PyliteSqlFileReader, PyliteSqlReaderError
from .output import get_valid_output_modes


COMMANDS = dict()


class DotCommandArgParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        raise KeyboardInterrupt


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def handle_dot_command(text, session):
    tokens = shlex.split(text)
    command = tokens[0]
    cmd_args = tokens[1:]

    try:
        command_obj = COMMANDS[command]
        command_obj.execute(cmd_args, session)
    except KeyError:
        eprint("Error: unrecognized command: {}".format(command))
        raise KeyboardInterrupt


def cmd(name):
    def wrapper(cls):
        COMMANDS[name] = cls(name)

        return cls

    return wrapper


class DotCommand(object):
    def __init__(self, name):
        self.name = name
        self.parser = self.get_parser()

    def execute(self, cmd_args, session):
        pass

    def get_parser(self):
        pass


@cmd(".quit")
class _DotQuit(DotCommand):
    def execute(self, cmd_args, session):
        raise EOFError

    def get_parser(self):
        parser = DotCommandArgParser(
            prog=self.name,
            usage="%(prog)s",
            description="Exit the program",
            add_help=False,
        )

        return parser


@cmd(".read")
class _DotRead(DotCommand):
    def execute(self, cmd_args, session):
        c_args = self.parser.parse_args(cmd_args)
        sql_file = c_args.FILE
        reader = PyliteSqlFileReader(sql_file)

        try:
            for sql in reader:
                result = session.connection.execute(sql)

                session.write_result(result)
        except PyliteSqlReaderError:
            eprint("Error: incomplete statement")

        raise KeyboardInterrupt

    def get_parser(self):
        parser = DotCommandArgParser(
            prog=self.name,
            description="Read input from FILE",
            add_help=False,
        )

        parser.add_argument("FILE")

        return parser


@cmd(".schema")
class _DotSchema(DotCommand):
    def execute(self, cmd_args, session):
        c_args = self.parser.parse_args(cmd_args)
        sql = "SELECT sql from sqlite_master WHERE type = 'table'"
        pattern = c_args.PATTERN

        if pattern is not None:
            sql += " AND name LIKE ?"
            result = session.connection.execute(sql, (pattern,))
        else:
            result = session.connection.execute(sql)

        for schema in result.fetchall():
            session.write_result(schema[0] + ";", mode="meta")

        raise KeyboardInterrupt

    def get_parser(self):
        parser = DotCommandArgParser(
            prog=self.name,
            add_help=False,
            description="Show the CREATE statements matching PATTERN",
        )

        parser.add_argument(
            "PATTERN",
            nargs="?",
            default=None,
        )

        return parser


@cmd(".tables")
class _DotTables(DotCommand):
    def execute(self, cmd_args, session):
        c_args = self.parser.parse_args(cmd_args)
        sql = "SELECT name FROM sqlite_master WHERE type = 'table'"
        table = c_args.TABLE

        if table is not None:
            sql += " AND name LIKE ?"
            result = session.connection.execute(sql, (table,))
        else:
            result = session.connection.execute(sql)

        for row in result.fetchall():
            session.write_result(row[0], mode="meta")

        raise KeyboardInterrupt

    def get_parser(self):
        parser = DotCommandArgParser(
            prog=self.name,
            add_help=False,
            description="List names of tables matching LIKE pattern PATTERN",
        )

        parser.add_argument("TABLE", nargs="?", default=None)

        return parser


@cmd(".prompt")
class _DotPrompt(DotCommand):
    def execute(self, cmd_args, session):
        c_args = self.parser.parse_args(cmd_args)
        new_message = c_args.PROMPT
        new_continuation = c_args.CONTINUATION

        if new_message is not None:
            session.message = new_message

        if new_continuation is not None:
            session.continuation = new_continuation

        raise KeyboardInterrupt

    def get_parser(self):
        parser = DotCommandArgParser(
            prog=self.name,
            add_help=False,
            description="Replace the standard prompts",
        )

        parser.add_argument("PROMPT", nargs="?", default=None)
        parser.add_argument("CONTINUATION", nargs="?", default=None)

        return parser


@cmd(".mode")
class _DotMode(DotCommand):
    def execute(self, cmd_args, session):
        c_args = self.parser.parse_args(cmd_args)
        mode = c_args.MODE

        if mode is not None:
            session.mode = mode

        raise KeyboardInterrupt

    def get_parser(self):
        parser = DotCommandArgParser(
            prog=self.name,
            add_help=False,
            description="Set the output mode",
        )

        parser.add_argument(
            "MODE", nargs="?", default=None, choices=get_valid_output_modes()
        )

        return parser


@cmd(".output")
class _DotOutput(DotCommand):
    def execute(self, cmd_args, session):
        c_args = self.parser.parse_args(cmd_args)
        dest = c_args.FILE
        session.dest = dest

        raise KeyboardInterrupt

    def get_parser(self):
        parser = DotCommandArgParser(
            prog=self.name,
            add_help=False,
            description="Send output to FILE or stdout if FILE is omitted",
        )

        parser.add_argument(
            "FILE", nargs="?", default="stdout", help="File to send output to"
        )

        return parser


@cmd(".dump")
class _DotDump(DotCommand):
    def execute(self, cmd_args, session):
        c_args = self.parser.parse_args(cmd_args)
        table_pattern = c_args.TABLE
        data_only = c_args.data_only
        connection = session.connection

        if table_pattern is not None:
            table_sql = (
                "SELECT name FROM sqlite_master " "WHERE type = 'table' AND name LIKE ?"
            )
            dump = []
            tables = connection.execute(table_sql, (table_pattern,)).fetchall()

            if not tables:
                raise KeyboardInterrupt

            if data_only is False:
                dump.append("BEGIN TRANSACTION;")

            for table in tables:
                table_name = table[0]

                if data_only is False:
                    schema_sql = (
                        "SELECT sql FROM sqlite_master "
                        "WHERE type = 'table' AND name = ?"
                    )
                    schema = connection.execute(schema_sql, (table_name,)).fetchone()

                    dump.append(schema[0] + ";")

                tbl_info = connection.execute(
                    "SELECT * FROM pragma_table_info(?)", (table_name,)
                )
                column_names = [str(row[1]) for row in tbl_info.fetchall()]
                quotes = ",".join(["'||quote(" + col + ")||'" for col in column_names])
                insert_statements_sql = (
                    "SELECT 'INSERT INTO {} VALUES(" + quotes + ");' FROM {}"
                ).format(table_name, table_name)
                insert_statements = connection.execute(insert_statements_sql)

                dump.extend([s[0] for s in insert_statements.fetchall()])

            if data_only is False:
                dump.append("COMMIT;")

            session.write_result("\n".join(dump), mode="meta")
        else:
            for line in session.connection.iterdump():
                session.write_result(line, mode="meta")

        raise KeyboardInterrupt

    def get_parser(self):
        parser = DotCommandArgParser(
            prog=self.name,
            add_help=False,
            description="Render database content as SQL",
        )

        parser.add_argument(
            "--data-only",
            action="store_true",
            help="Output INSERT statements only",
        )
        parser.add_argument(
            "TABLE",
            nargs="?",
            help="A LIKE pattern specifying the table to dump",
        )

        return parser


@cmd(".help")
class _DotHelp(DotCommand):
    def execute(self, cmd_args, session):
        c_args = self.parser.parse_args(cmd_args)
        topic_pattern = c_args.PATTERN
        show_all = c_args.all or not topic_pattern

        if show_all:
            topics = sorted(COMMANDS.keys())
        else:
            if topic_pattern.startswith(".") is False:
                topic_pattern = "." + topic_pattern

            topics = filter(
                lambda c: c.startswith(topic_pattern), sorted(COMMANDS.keys())
            )

        if not topics:
            eprint("Nothing matches '{}'".format(topic_pattern))
            raise KeyboardInterrupt

        for t in topics:
            text = FormattedText([("#C560FF", t)])

            print_formatted_text(text, file=session.dest)
            COMMANDS[t].parser.print_help(session.dest)
            session.write_result("", mode="meta")

        raise KeyboardInterrupt

    def get_parser(self):
        parser = DotCommandArgParser(
            prog=self.name,
            add_help=False,
            description="Show help text for PATTERN",
        )

        parser.add_argument(
            "PATTERN",
            nargs="?",
            help="Topic pattern to print help for",
        )
        parser.add_argument(
            "--all",
            action="store_true",
        )

        return parser
