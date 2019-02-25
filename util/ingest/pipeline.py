"""
Wrap individual data ingestion steps into something application-specific


0. Confirm that the file can be read (text or bgzipped format)
1. Validate that a GWAS file is valid and acceptable: has all columns; known chromosomes; pvals not missing or 0;
    data is sorted
    1a. - (optional) Validate build identifier (pheweb detect-ref) -
        TODO: this relies on a large data file that has to be built after install, which is not docker-friendly. We'll
          delay integrating this feature until improved.
    1b. Convert the GWAS file to normalized, tabixed, gzipped format
3. Generate data needed for binned manhattan plot + QQ plot.
4. (optional?) Find a list of top hits in each region, based on some algorithm/ criteria
"""


import logging

from . import (
    helpers,
    processors,
    validators
)


logger = logging.getLogger(__name__)


@helpers.capture_errors
def standard_gwas_pipeline(
    src_path: str,
    normalized_path: str,
    normalize_log_path: str,
    manhattan_path: str,
    qq_path: str,
) -> bool:
    # - Validate file format (ingest.validators)
    # - normalized.gz- Write a cleaned, tabix-compressed version of the file that represents the data we can read
    #   (zorp.reader.write)
    #     - normalize.log Track the output of the conversion script
    # - manhattan.json - Make manhattan plot json file
    # - qq.json - Make QQ plot json file

    # TODO: Better communicate which step of the pipeline failed
    if not validators.standard_gwas_validator.validate(src_path):
        logger.info("Could not load GWAS '{}' because contents failed to validate".format(src_path))
        return False

    # For now the writer expects a temp file name, and it creates the .gz version internally # TODO: This is silly
    tmp_normalized_path = normalized_path.replace('.txt.gz', '.txt')
    if not processors.normalize_contents(src_path, tmp_normalized_path, normalize_log_path):
        return False

    return all([
        processors.generate_manhattan(normalized_path, manhattan_path),
        processors.generate_qq(normalized_path, qq_path),
    ])
