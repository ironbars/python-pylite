from prompt_toolkit import PromptSession
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer

from .input import PyliteSqlPromptReader


class PylitePromptSession(object):
    def __init__(self):
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

