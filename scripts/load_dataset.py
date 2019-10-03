"""
A sample script that can be used to load a real dataset from a GWAS file on disk. Covers creating a
    sample data file + metadata, copying it over to the `MEDIA_ROOT` uploads directory, and starting the celery ingest
    pipeline. Running this script requires that the app be running already in a separate container.

    Sample usage (to be improved later):
    `docker-compose -f local.yml run --rm django python3 scripts/load_dataset.py`
"""

import os
from pathlib import Path
import sys

import django
from django.core.files import File

# Must configure standalone django usage before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
sys.path.append(str(Path(__file__).parent.parent.resolve()))
django.setup()


from locuszoom_plotting_service.gwas.models import (
    AnalysisInfo,
    AnalysisFileset,
    User
) # noqa


def ingest_from_local(owner_id: int, path_to_file: str,
                      label: str, study_name: str, genome_build, parser_options: dict, *,
                      pmid=None, public=False) -> str:
    # Note: parser_options must be a dict of zorp-compatible kwargs (to `GenericGWASLineParser`).
    #   In that syntax, columns are human-friendly (1-indexed)
    #  https://github.com/abought/zorp/blob/develop/zorp/parsers.py#L123
    owner = User.objects.get(pk=owner_id)
    instance = AnalysisInfo(
        # For bulk ingest, we'd likely be uploading on behalf of an admin user
        #   (when in doubt pick a low number: 1, 2, etc)
        owner=owner,
        label=label,
        study_name=study_name,
        pmid=pmid,
        build=genome_build,
        is_public=public
    )
    instance.save()

    # One edge case: this assumes that both metadata and the file will always save successfully. If this fails, we'll
    #   have an extra DB record that never went on to process a file. Annoying but not inherently fatal.
    with open(path_to_file, 'rb') as f:
        raw_file = File(f)
        file_instance = AnalysisFileset(
            parser_options=parser_options,
            raw_gwas_file=raw_file,
            metadata=instance
        )
        file_instance.save()

    # Return the identifier that would be used to access this GWAS from the web
    return instance.slug


if __name__ == '__main__':
    # In local development, the local directory is bind-mounted to /app, which makes it easy for the server to
    #   be aware of files that need ingesting
    # In production, the script might need a little help to find the data (TBD)
    ingest_from_local(
        1,
        '/app/deleteme/dataset.tab.gz',
        'A sample GWAS',
        'BlameRyan Consortium',
        'GRCh37',
        parser_options={
            "chrom_col": 1,
            "pos_col": 3,
            "ref_col": 6,
            "alt_col": 7,
            "pvalue_col": 11,
            "is_neg_log_pvalue": False,
            "beta_col": 9,
            "stderr_beta_col": 10,
            "allele_freq_col": 8,
            "is_alt_effect": True,
        }
    )
