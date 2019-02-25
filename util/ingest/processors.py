"""
Steps used to process a GWAS file for future use
"""
import json
import logging
import typing as ty

from pheweb.load import (
    manhattan,
    qq,
)

from util.zorp import exceptions as z_exc
from .exceptions import ManhattanExeption, QQPlotException, UnexpectedIngestException
from . loaders import make_reader
from . import helpers

logger = logging.getLogger(__name__)


@helpers.capture_errors
def normalize_contents(src_path: str, dest_path: str, log_path: str) -> bool:
    """
    Initial content ingestion: load the file and write variants in a standardized format

    This routine will deliberately exclude lines that could not be handled in a reliable fashion, such as pval=NA
    """
    reader = make_reader(src_path)

    success = False
    try:
        dest_fn = reader.write(dest_path, make_tabix=True)
    except z_exc.TooManyBadLinesException as e:
        raise e
    else:
        success = True
        logger.info('Conversion succeeded! Results written to: {}'.format(dest_fn))
    finally:
        # Always write a log entry, no matter what
        with open(log_path, 'w') as f:
            for n, reason, _ in reader.errors:
                f.write('Excluded row {} from output due to parse error: {}\n'.format(n, reason))

            if success:
                f.write('[success] GWAS file has been converted.\n')
                return True
            else:
                f.write('[failure] Could not create normalized GWAS file for: {}'.format(src_path))


@helpers.capture_errors
def _pheweb_adapter(reader) -> ty.Iterator[dict]:
    """Formats zorp parsed data into the format expected by pheweb"""
    for row in reader:
        yield {'chrom': row.chrom, 'pos': row.pos, 'pval': row.pvalue}


@helpers.capture_errors
def generate_manhattan(in_filename: str, out_filename: str) -> bool:
    """Generate manhattan plot data for the processed file"""
    reader = make_reader(in_filename).add_filter("pvalue", lambda v, row: v is not None )
    reader_adapter = _pheweb_adapter(reader)

    binner = manhattan.Binner()
    for variant in reader_adapter:
        binner.process_variant(variant)

    manhattan_data = binner.get_result()

    # TODO: consider using boltons.atomicsaver in future
    with open(out_filename, 'w') as f:
        json.dump(manhattan_data, f)
    return True


@helpers.capture_errors
def generate_qq(in_filename: str, out_filename) -> bool:
    """Largely borrowed from PheWeb code (load.qq.make_json_file)"""
    # TODO: Currently the ingest pipeline never stores "af"/"maf" at all, which could affect this calculation
    # TODO: This step appears to load ALL data into memory (list on generator). This could be a memory hog; not sure if
    #   there is a way around it as it seems to rely on sorting values
    reader = make_reader(in_filename).add_filter("pvalue", lambda v, row: v is not None)
    reader_adapter = _pheweb_adapter(reader)

    # TODO: Pheweb QQ code benefits from being passed { num_samples: n }, from metadata stored outside the
    #   gwas file. This is used when AF/MAF are present (which at the moment ingest pipeline does not support)
    stub = {}

    variants = list(qq.augment_variants(reader_adapter, stub))

    rv = {}
    if variants:
        if variants[0].maf is not None:
            rv['overall'] = qq.make_qq_unstratified(variants, include_qq=False)
            rv['by_maf'] = qq.make_qq_stratified(variants)
            rv['ci'] = list(qq.get_confidence_intervals(len(variants) / len(rv['by_maf'])))
        else:
            rv['overall'] = qq.make_qq_unstratified(variants, include_qq=True)
            rv['ci'] = list(qq.get_confidence_intervals(len(variants)))

    with open(out_filename, 'w') as f:
        json.dump(rv, f)

    return True
