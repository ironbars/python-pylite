class PyliteException(Exception):
    pass


class REPLResetEvent(PyliteException):
    pass


class SQLReaderError(PyliteException):
    pass
