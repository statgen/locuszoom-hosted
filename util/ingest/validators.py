"""Perform simple sanity checks to make sure the uploaded file is valid and readable"""

import itertools
import logging

import magic

from zorp import (
    parsers,
    sniffers
)
from zorp.readers import BaseReader

from . import (
    exceptions as v_exc, helpers
)


logger = logging.getLogger(__name__)


class _GwasValidator:
    """Validate a raw GWAS file as initially uploaded (given filename and instructions on how to parse it)"""
    def __init__(self, headers=None, delimiter='\t'):
        self._delimiter = delimiter
        self._headers = headers

    @helpers.capture_errors
    def validate(self, filename: str, parser_options: dict) -> bool:
        """Perform all checks for a stored file"""
        encoding = self._get_encoding(filename)

        # Create a reader than can handle the filetype and header format of whatever the user uploads
        parser = parsers.GenericGwasLineParser(**parser_options)
        reader = sniffers.guess_gwas_generic(filename, parser=parser)
        return all([
            self._validate_mimetype(encoding),
            self._validate_contents(reader),
        ])

    def _get_encoding(self, filename: str) -> str:
        return magic.from_file(filename, mime=True)

    @helpers.capture_errors
    def _validate_mimetype(self, mimetype: str) -> bool:
        """Uploaded either a gzipped file or plain text"""
        if (mimetype in ['application/gzip', 'application/x-gzip']) or mimetype.startswith('text/'):
            return True
        else:
            raise v_exc.ValidationException(f'Only plaintext or gzipped files are accepted. Your file is: {mimetype}')

    @helpers.capture_errors
    def _validate_data_rows(self, reader) -> bool:
        """Data must be sorted, all values must be readable, and all chroms must be known"""
        # Horked from PheWeb's `load.read_input_file.PhenoReader` class
        cp_groups = itertools.groupby(reader, key=lambda v: (v.chrom, v.pos))

        prev_chrom = None
        prev_pos = -1
        for cp, tied_variants in cp_groups:
            cur_chrom = cp[0]
            if cur_chrom == prev_chrom and cp[1] < prev_pos:
                # Positions not in correct order for Pheweb to use
                raise v_exc.ValidationException('Positions must be sorted prior to uploading')

            prev_chrom = cur_chrom
            prev_pos = cp[1]

        # Must make it through the entire file without parsing errors, with all chroms in order, and find at least
        #   one row of data
        if prev_pos != -1:
            return True
        else:
            raise v_exc.ValidationException('File must contain at least one row of data')

    @helpers.capture_errors
    def _validate_contents(self, reader: BaseReader) -> bool:
        """Validate file contents; useful for unit testing"""
        return self._validate_data_rows(reader)


standard_gwas_validator = _GwasValidator(delimiter='\t')
