from sqlite3 import Connection
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer

from pylite.input import PyliteSqlPromptReader
from pylite.output import PyliteSqlResultWriter


class PylitePromptSession(object):
    def __init__(self, connection: Connection) -> None:
        self.connection = connection
        self.style = Style.from_dict(
            {
                "pygments.keyword": "#33C3FF",
                "pygments.literal.string": "#FF5833",
            }
        )
        self.session = PromptSession(
            lexer=PygmentsLexer(SqlLexer),
            style=self.style,
            include_default_pygments_style=False,
        )
        self.reader = PyliteSqlPromptReader(self.session)
        self.writer = PyliteSqlResultWriter()

    def prompt(self) -> str:
        text = self.reader.prompt()

        return text

    def write_result(self, data: Any, mode: str | None = None) -> None:
        self.writer.write_result(data, mode)

    @property
    def message(self) -> str:
        return self.reader.message

    @message.setter
    def message(self, new_message: str):
        self.reader.message = new_message

    @message.deleter
    def message(self) -> None:
        self.reader.message = "pylite> "

    @property
    def continuation(self) -> str:
        return self.reader.continuation

    @continuation.setter
    def continuation(self, new_continuation: str) -> None:
        self.reader.continuation = new_continuation

    @continuation.deleter
    def continuation(self) -> None:
        self.reader.continuation = "   ...> "

    @property
    def mode(self) -> str:
        return self.writer.mode

    @mode.setter
    def mode(self, new_mode: str) -> None:
        self.writer.mode = new_mode

    @mode.deleter
    def mode(self):
        del self.writer.mode

    @property
    def dest(self) -> str:
        return self.writer.dest

    @dest.setter
    def dest(self, new_dest: str) -> None:
        self.writer.dest = new_dest

    @dest.deleter
    def dest(self):
        del self.writer.dest

    @property
    def colsep(self) -> str:
        return self.writer.colsep

    @colsep.setter
    def colsep(self, new_colsep: str) -> None:
        self.writer.colsep = new_colsep

    @property
    def rowsep(self) -> str:
        return self.writer.rowsep

    @rowsep.setter
    def rowsep(self, new_rowsep: str) -> None:
        self.writer.rowsep = new_rowsep
