from prompt_toolkit import PromptSession

from pylite.exceptions import SQLReaderError
from pylite.input.reader import SQLReader

DEFAULT_PROMPT_MESSAGE = "pylite> "
DEFAULT_PROMPT_CONTINUATION = "   ...> "


class SQLPromptReader(SQLReader):
    def __init__(
        self,
        source: PromptSession | None,
        message: str = DEFAULT_PROMPT_MESSAGE,
        continuation: str = DEFAULT_PROMPT_CONTINUATION,
    ) -> None:
        if source is None:
            raise SQLReaderError("'source' cannot be None for SQLPromptReader")

        self.message = message
        self.continuation = continuation

        super().__init__(source)

    def prompt(self) -> str:
        assert self.source is not None  # to appease mypy

        text = self.source.prompt(self.message)

        if text.startswith("."):
            return text

        return self.build_complete_statement(text, self.source)

    def get_next(self, sql_src: PromptSession) -> str:
        return sql_src.prompt(self.continuation)
