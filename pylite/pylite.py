#!/usr/bin/python3

import sys
import sqlite3

from prompt_toolkit import PromptSession
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer
from tabulate import tabulate

def main(database):
    style = Style.from_dict({
        "pygments.keyword": "#33C3FF",
        "pygments.literal.string": "#FF5833",
    })
    connection = sqlite3.connect(database)
    session = PromptSession(
        lexer=PygmentsLexer(SqlLexer), 
        style=style, 
        include_default_pygments_style=False)

    while True:
        try:
            text = session.prompt('> ')
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
                headers = tuple(col[0] for col in messages.description)

                print(tabulate(messages, headers=headers, tablefmt='grid'))
                #print(header)

                #for message in messages:
                #    print(message)

    print('GoodBye!')

