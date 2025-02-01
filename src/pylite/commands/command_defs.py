import shlex
from sqlite3 import OperationalError
from typing import Callable, Type, TypeVar

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText

from pylite.commands.dot_command import DotCommand, DotCommandArgParser
from pylite.commands.registry import cmd_registry
from pylite.exceptions import REPLResetEvent, SQLReaderError
from pylite.input import SQLFileReader
from pylite.output import get_valid_output_modes
from pylite.session import PylitePromptSession


def handle_dot_command(text: str, session: PylitePromptSession):
    tokens = shlex.split(text)
    command = tokens[0]
    cmd_args = tokens[1:]

    try:
        cmd_registry.get(command).execute(cmd_args, session)
    except KeyError:
        session.write_error(f"Error: unrecognized command: {command}")
        raise REPLResetEvent


T = TypeVar("T", bound=DotCommand)


def cmd(name: str) -> Callable[[Type[T]], Type[T]]:
    def wrapper(cls: Type[T]) -> Type[T]:
        cmd_registry.register(name, cls(name))

        return cls

    return wrapper


@cmd(".quit")
class _DotQuit(DotCommand):
    def execute(self, cmd_args: list[str], session: PylitePromptSession) -> None:
        raise EOFError

    def get_parser(self) -> DotCommandArgParser:
        parser = DotCommandArgParser(
            prog=self.name,
            usage="%(prog)s",
            description="Exit the program",
            add_help=False,
        )

        return parser


@cmd(".read")
class _DotRead(DotCommand):
    def execute(self, cmd_args: list[str], session: PylitePromptSession) -> None:
        c_args = self.parser.parse_args(cmd_args)
        sql_file = c_args.FILE
        reader = SQLFileReader(sql_file)

        try:
            for sql in reader:
                result = session.connection.execute(sql)

                session.write_result(result)
        except SQLReaderError:
            session.write_error("Error: incomplete statement")

        raise REPLResetEvent

    def get_parser(self) -> DotCommandArgParser:
        parser = DotCommandArgParser(
            prog=self.name,
            description="Read input from FILE",
            add_help=False,
        )

        parser.add_argument("FILE")

        return parser


@cmd(".schema")
class _DotSchema(DotCommand):
    def execute(self, cmd_args: list[str], session: PylitePromptSession) -> None:
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

        raise REPLResetEvent

    def get_parser(self) -> DotCommandArgParser:
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
    def execute(self, cmd_args: list[str], session: PylitePromptSession) -> None:
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

        raise REPLResetEvent

    def get_parser(self) -> DotCommandArgParser:
        parser = DotCommandArgParser(
            prog=self.name,
            add_help=False,
            description="List names of tables matching LIKE pattern PATTERN",
        )

        parser.add_argument("TABLE", nargs="?", default=None)

        return parser


@cmd(".prompt")
class _DotPrompt(DotCommand):
    def execute(self, cmd_args: list[str], session: PylitePromptSession) -> None:
        c_args = self.parser.parse_args(cmd_args)
        new_message = c_args.PROMPT
        new_continuation = c_args.CONTINUATION

        if new_message is not None:
            session.message = new_message

        if new_continuation is not None:
            session.continuation = new_continuation

        raise REPLResetEvent

    def get_parser(self) -> DotCommandArgParser:
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
    def execute(self, cmd_args: list[str], session: PylitePromptSession) -> None:
        c_args = self.parser.parse_args(cmd_args)
        mode = c_args.MODE

        if mode is not None:
            session.mode = mode

        raise REPLResetEvent

    def get_parser(self) -> DotCommandArgParser:
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
    def execute(self, cmd_args: list[str], session: PylitePromptSession) -> None:
        c_args = self.parser.parse_args(cmd_args)
        dest = c_args.FILE
        session.dest = dest

        raise REPLResetEvent

    def get_parser(self) -> DotCommandArgParser:
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
    def execute(self, cmd_args: list[str], session: PylitePromptSession) -> None:
        c_args = self.parser.parse_args(cmd_args)
        table_pattern = c_args.TABLE
        data_only = c_args.data_only
        connection = session.connection

        if table_pattern is not None:
            table_sql = (
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE ?"
            )
            dump = []
            tables = connection.execute(table_sql, (table_pattern,)).fetchall()

            if not tables:
                raise REPLResetEvent

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
                    f"SELECT 'INSERT INTO {table_name} VALUES("
                    + quotes
                    + ");' FROM {table_name}"
                )
                insert_statements = connection.execute(insert_statements_sql)

                dump.extend([s[0] for s in insert_statements.fetchall()])

            if data_only is False:
                dump.append("COMMIT;")

            session.write_result("\n".join(dump), mode="meta")
        else:
            for line in session.connection.iterdump():
                session.write_result(line, mode="meta")

        raise REPLResetEvent

    def get_parser(self) -> DotCommandArgParser:
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


@cmd(".databases")
class _DotDatabases(DotCommand):
    def execute(self, cmd_args: list[str], session: PylitePromptSession) -> None:
        sql = "PRAGMA database_list;"
        result = session.connection.execute(sql).fetchall()

        for seq, name, file in result:
            try:
                # This value is coming from the database and should be safe to format
                # Also, this is a reliable way to tell if a SQLite database is writeable
                # user_version will always be 0 (unless you've changed it), so this
                # pragma has no effect.  It will, however, throw an exception if the
                # database was opened RO.
                session.connection.execute(f"PRAGMA {name}.user_version=0")
                writeable = True
            except OperationalError:  # Not writeable
                writeable = False

            perms = "r/w" if writeable else "r/o"
            file = file or '""'

            session.write_result(f"{name}: {file} {perms}", mode="meta")

        raise REPLResetEvent

    def get_parser(self) -> DotCommandArgParser:
        parser = DotCommandArgParser(
            prog=self.name,
            add_help=False,
            description="List names and files of attached databases",
        )

        return parser


@cmd(".help")
class _DotHelp(DotCommand):
    def execute(self, cmd_args: list[str], session: PylitePromptSession) -> None:
        c_args = self.parser.parse_args(cmd_args)
        topic_pattern = c_args.PATTERN
        show_all = c_args.all or not topic_pattern

        if show_all:
            topics = sorted(cmd_registry.get_all())
        else:
            if not topic_pattern.startswith("."):
                topic_pattern = "." + topic_pattern

            topics = [
                c for c in cmd_registry.get_all() if c.startswith(topic_pattern.lower())
            ]

        if not topics:
            session.write_error(f"Nothing matches '{topic_pattern}'")
            raise REPLResetEvent

        for t in topics:
            text = FormattedText([("#C560FF", t)])

            print_formatted_text(text, file=session.dest)
            cmd_registry.get(t).parser.print_help(session.dest)
            session.write_result("", mode="meta")

        raise REPLResetEvent

    def get_parser(self) -> DotCommandArgParser:
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
