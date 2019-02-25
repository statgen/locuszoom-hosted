"""
Utility functions for upload pipeline
"""

import os

from django.conf import settings


def get_study_folder(instance, *args, absolute_path=False):
    """
    A single uploaded file is processed to yield several output files, which live in a folder on disk.
    """
    relative = str(instance.pipeline_path)
    if absolute_path:
        # Some django functionality (eg DB filefields) transparently adds MEDIA_ROOT to path.
        #   For files not directly known to the model, we'll need to refer to the filesystem directly.
        return os.path.join(settings.MEDIA_ROOT, relative)
    else:
        return relative


def get_gwas_raw_fn(instance, filename):
    """Used only on initial upload; afterwards, all access to the raw file will be through a model field"""
    # FIXME: Audit this for path issues, eg a gwas filename with relative path fields (`../../gwas.json`)
    _, ext = os.path.splitext(filename)
    out_fn = os.path.join(
        get_study_folder(instance),
        'raw_gwas' + ext
    )
    return out_fn
