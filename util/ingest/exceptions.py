"""
Custom exceptions describing pipeline errors
"""


class BaseIngestException(Exception):
    DEFAULT_MESSAGE: str

    def __init__(self, message=None, *args):
        super(BaseIngestException, self).__init__(*args)
        self.message = message or self.DEFAULT_MESSAGE

    def __str__(self):
        return str(self.message)


class UnexpectedIngestException(BaseIngestException):
    DEFAULT_MESSAGE = 'An unexpected error has occurred'


class ValidationException(BaseIngestException):
    DEFAULT_MESSAGE = 'Validation failed'


class ManhattanExeption(BaseIngestException):
    DEFAULT_MESSAGE = 'Could not generate Manhattan plot'


class TopHitException(BaseIngestException):
    DEFAULT_MESSAGE = 'No top hit could be found'


class QQPlotException(BaseIngestException):
    DEFAULT_MESSAGE = 'Could not generate QQ plot'
