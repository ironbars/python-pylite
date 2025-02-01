from pylite.commands.dot_command import DotCommand


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, DotCommand] = dict()

    def register(self, name: str, command: DotCommand) -> None:
        self._commands[name] = command

    def get(self, name: str) -> DotCommand:
        return self._commands[name]

    def get_all(self) -> list[str]:
        return list(self._commands.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._commands


cmd_registry = CommandRegistry()
