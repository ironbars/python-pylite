from prompt_toolkit import PromptSession
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer

from .input import PyliteSqlPromptReader


class PylitePromptSession(object):
    def __init__(self, connection):
        self.connection = connection
        self.style = Style.from_dict({
            "pygments.keyword": "#33C3FF",
            "pygments.literal.string": "#FF5833",
        })
        self.session = PromptSession(
            lexer=PygmentsLexer(SqlLexer),
            style=self.style,
            include_default_pygments_style=False
        )
        self.reader = PyliteSqlPromptReader(self.session)


    def prompt(self):
        text = self.reader.prompt()

        return text


    @property
    def message(self):
        return self.reader.message


    @message.setter
    def message(self, new_message):
        self.reader.message = new_message


    @message.deleter
    def message(self):
        self.reader.message = "pylite> "


    @property
    def continuation(self):
        return self.reader.continuation


    @continuation.setter
    def continuation(self, new_continuation):
        self.reader.continuation = new_continuation


    @continuation.deleter
    def continuation(self):
        self.reader.continuation = "   ...> "

