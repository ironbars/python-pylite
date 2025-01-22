#!/usr/bin/python3

import sys
import sqlite3

from .session import PylitePromptSession
from .commands import handle_dot_command


def main(database):
    session = PylitePromptSession(connection=sqlite3.connect(database))

    while True:
        try:
            text = session.prompt()

            if text.startswith("."):
                handle_dot_command(text, session)
        except KeyboardInterrupt:
            continue  # Control-C pressed. Try again.
        except EOFError:
            break  # Control-D pressed.

        with session.connection:
            try:
                messages = session.connection.execute(text)
            except Exception as e:
                print(repr(e))
            else:
                session.write_result(messages)

    print("GoodBye!")
