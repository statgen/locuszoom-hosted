import random

from django.db import models


def _generate_slug():
    """Generate a random 6-digit string, for use as "slugs" (external-facing record IDs)"""
    return str(random.randrange(1, 1e6, 1))
