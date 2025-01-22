#!/usr/bin/python3

import sqlite3
import sys

from prompt_toolkit import print_formatted_text, HTML

from pylite.commands import handle_dot_command
from pylite.session import PylitePromptSession


def welcome(database: str) -> None:
    if database == ":memory:":
        db_msg = "You are connected to a <b>transient, in memory database</b>."
    else:
        db_msg = ""

    base_msg = "Welcome to <ansigreen>pylite</ansigreen>!"
    usage_msg = "Enter \"<violet>.help</violet>\" for usage hints."

    msg = HTML("\n".join([base_msg, usage_msg, db_msg]))

    print_formatted_text(msg)
    

def repl(database):
    session = PylitePromptSession(connection=sqlite3.connect(database))

    welcome(database)

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
