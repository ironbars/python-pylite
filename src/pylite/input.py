import os
from sqlite3 import complete_statement


class PyliteSqlReaderError(Exception):
    pass


class PyliteSqlReader:
    def __init__(self, source=None):
        self.source = source

    def build_complete_statement(self, text, sql_src):
        statement_components = []
        statement_terminated = complete_statement(text)

        if statement_terminated:
            return text

        while statement_terminated is False:
            statement_components.append(text)

            if complete_statement(text):
                statement_terminated = True
            else:
                text = self.get_next(sql_src)

        return " ".join(statement_components)

    def get_next(self, sql_src):
        pass


class PyliteSqlFileReader(PyliteSqlReader):
    def __init__(self, source):
        self.sql = []

        if not os.path.exists(source):
            raise PyliteSqlReaderError("File doesn't exist or is not readable")

        super().__init__(source)

    def __iter__(self):
        with open(self.source, "r") as sf:
            sql_gen = (line.split("--")[0].strip() for line in sf)

            try:
                for line in sql_gen:
                    if not line:
                        continue

                    yield self.build_complete_statement(line, sql_gen)
            except StopIteration:
                raise PyliteSqlReaderError("Incomplete statement")

    def get_next(self, sql_src):
        return next(sql_src)

    # Not quite sure the use case of this, but I kind of like having it here
    def load_sql(self):
        self.sql = [line for line in self]

        return self.sql


class PyliteSqlPromptReader(PyliteSqlReader):
    def __init__(self, source, message="pylite> ", continuation="   ...> "):
        self.message = message
        self.continuation = continuation

        super().__init__(source)

    def prompt(self):
        text = self.source.prompt(self.message)

        if text.startswith("."):
            return text

        return self.build_complete_statement(text, self.source)

    def get_next(self, sql_src):
        return sql_src.prompt(self.continuation)
