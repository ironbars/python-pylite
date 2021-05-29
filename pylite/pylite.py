#!/usr/bin/python3

import sys
import sqlite3

#from prompt_toolkit import PromptSession
#from prompt_toolkit.lexers import PygmentsLexer
#from prompt_toolkit.styles import Style
#from pygments.lexers.sql import SqlLexer

from .session import PylitePromptSession
from .commands import handle_dot_command
from .output import print_result


def main(database):
    #style = Style.from_dict({
        #"pygments.keyword": "#33C3FF",
        #"pygments.literal.string": "#FF5833",
    #})
    connection = sqlite3.connect(database)
    session = PylitePromptSession()
    #session = PromptSession(
        #lexer=PygmentsLexer(SqlLexer), 
        #style=style, 
        #include_default_pygments_style=False)

    while True:
        try:
            text = session.prompt()

            if text.startswith("."):
                handle_dot_command(text, connection)
        except KeyboardInterrupt:
            continue  # Control-C pressed. Try again.
        except EOFError:
            break  # Control-D pressed.

        with connection:
            try:
                messages = connection.execute(text)
            except Exception as e:
                print(repr(e))
            else:
                print_result(messages)

    print('GoodBye!')

