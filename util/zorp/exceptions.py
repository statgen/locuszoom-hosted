"""
Exceptions related to reading and parsing data
"""


class BaseZorpException(Exception):
    DEFAULT_MESSAGE: str

    def __init__(self, message=None, *args):
        super(BaseZorpException, self).__init__(*args)
        self.message = message or self.DEFAULT_MESSAGE

    def __str__(self):
        return str(self.message)


class ConfigurationException(BaseZorpException):
    DEFAULT_MESSAGE = "Invalid option specified"


class SnifferException(BaseZorpException):
    DEFAULT_MESSAGE = 'Could not auto-detect file format'


class LineParseException(BaseZorpException):
    """An error occurred while parsing a single line. Capture the data that failed to parse for context."""
    DEFAULT_MESSAGE = "Could not parse specified line"

    def __init__(self, *args, line=None, ):
        super(LineParseException, self).__init__(*args)
        self.line = line


class TooManyBadLinesException(BaseZorpException):
    DEFAULT_MESSAGE = "Too many lines in the file failed to parse; stopping"

    def __init__(self, *args, error_list: list = None, **kwargs):
        super(TooManyBadLinesException, self).__init__(*args)
        self.error_list = error_list
