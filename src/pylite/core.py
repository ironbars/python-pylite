import sqlite3

from prompt_toolkit import HTML, print_formatted_text

from pylite.commands import handle_dot_command
from pylite.exceptions import REPLResetEvent
from pylite.session import PylitePromptSession


def generate_welcome_message(database: str) -> HTML:
    base_msg = "Welcome to <ansigreen>pylite</ansigreen>!"
    usage_msg = 'Enter "<violet>.help</violet>" for usage hints.'

    if database == ":memory:":
        db_msg = "You are connected to a <b>transient, in memory database</b>."
    else:
        db_msg = f"Connected to database: <b>{database}</b>."

    parts = [base_msg, usage_msg, db_msg]
    full_msg = "\n".join(filter(None, parts))

    return HTML(full_msg)


def welcome(database: str) -> None:
    msg = generate_welcome_message(database)

    print_formatted_text(msg)


def repl(database: str) -> None:
    session = PylitePromptSession(connection=sqlite3.connect(database))

    welcome(database)

    while True:
        try:
            text = session.prompt()

            if text.startswith("."):
                handle_dot_command(text, session)
        except REPLResetEvent:
            continue  # Normal app execution
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

    session.connection.close()
    print("\nGoodBye!")
