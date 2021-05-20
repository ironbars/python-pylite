from sqlite3 import complete_statement


class PyliteSqlReaderError(Exception):
    pass


class PyliteSqlReader(object):
    def __init__(self, sql_file):
        self.sql_file = sql_file
        self.sql = []


    def __iter__(self):
        with open(self.sql_file, "r") as sf:
            statement_components = []
            statement_terminated = False
            sql_gen = self._strip_sql_comments(sf)

            try:
                for line in sql_gen:
                    if not line:
                        continue

                    while statement_terminated is False:
                        statement_components.append(line)

                        if complete_statement(line):
                            statement_terminated = True
                        else:
                            line = next(sql_gen)

                    yield " ".join(statement_components)

                    statement_terminated = False
                    statement_components = []
            except StopIteration:
                raise PyliteSqlReaderError("Incomplete statement")


    def _strip_sql_comments(self, f):
        for line in f:
            yield line.split("--")[0].strip()


    # Not quite sure the use case of this, but I kind of like having it here
    def load_sql(self):
        self.sql = [line for line in self]

        return self.sql

