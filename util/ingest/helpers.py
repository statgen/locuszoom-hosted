"""
Generic helper methods
"""

import functools
import logging
import re
import typing as ty

from . import exceptions
from zorp import exceptions as z_exc

logger = logging.getLogger(__name__)


def capture_errors(func):
    """
    Log errors internally, but display a more generic error to the user

    Useful for pipelines and validators that need to report success/failure.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (exceptions.BaseIngestException, z_exc.BaseZorpException):
            # If we already provide a useful validation message, use that
            raise
        except Exception:
            # Any totally unhandled problems get a bland error message and are recorded
            logger.exception('Task failed due to unexpected error')
            raise exceptions.UnexpectedIngestException
    return wrapper


def natural_sort(items: ty.Iterable):
    """Natural sort a list of strings. Used for human-friendly error messages, eg, from a `set` of allowed strings"""
    convert = lambda text: int(text) if text.isdigit() else text.lower()  # noqa: E731
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]  # noqa: E731
    return sorted(items, key=alphanum_key)
