import os

COMMANDS = dict()


def handle_dot_command(text, connection):
    tokens = text.split()
    command = tokens[0]
    args = tokens[1:]

    try:
        COMMANDS[command](args, connection)
    except KeyError:
        print("Unrecognized command: {}".format(command))


def cmd(name):
    def wrapper(func):
        COMMANDS[name] = func

        return func
    return wrapper


@cmd(".quit")
def _quit(args, connection):
    raise EOFError

