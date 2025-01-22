#!/usr/bin/python3

import sqlite3
import sys

from pylite.commands import handle_dot_command
from pylite.session import PylitePromptSession


def repl(database):
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
