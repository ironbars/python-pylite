#!/usr/bin/python3

import sys
import sqlite3

from .session import PylitePromptSession
from .commands import handle_dot_command
from .output import print_result


def main(database):
    connection = sqlite3.connect(database)
    session = PylitePromptSession()

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

