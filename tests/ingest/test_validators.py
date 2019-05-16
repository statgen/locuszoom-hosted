import os

import pytest

from util.ingest import (
    exceptions as val_exc, validators
)

from zorp import (
    parsers, readers
)


class TestStandardGwasValidator:
    def test_valid_input(self):
        reader = readers.IterableReader([
            "#chrom\tpos\tref\talt\tpvalue",
            "1\t1\tA\tC\t7.3",
            "X\t1\tA\tC\t7.3",
        ], parser=parsers.standard_gwas_parser, skip_rows=1)

        is_valid = validators.standard_gwas_validator._validate_contents(reader)
        assert is_valid

    def test_wrong_datatype(self):
        reader = readers.IterableReader([
            "#chrom\tpos\tref\talt\tpvalue",
            "1\t1\tA\tC\t7.3",
            "X\t1\tA\tC\tNOPE"
        ], parser=parsers.standard_gwas_parser, skip_rows=1)

        with pytest.raises(Exception):
            validators.standard_gwas_validator._validate_contents(reader)

    @pytest.mark.skip(reason="Unclear whether this is actually a requirement for PheWeb loaders; revisit")
    def test_wrong_chrom_order(self):
        reader = readers.IterableReader([
            "#chrom\tpos\tref\talt\tpvalue",
            "2\t1\tA\tC\t7.3",
            "1\t1\tA\tC\t7.3"
        ], parser=parsers.standard_gwas_parser, skip_rows=1)

        with pytest.raises(val_exc.ValidationException):
            validators.standard_gwas_validator._validate_contents(reader)

    @pytest.mark.skip
    def test_chroms_not_sorted(self):
        reader = readers.IterableReader([
            "#chrom\tpos\tref\talt\tpvalue",
            "1\t1\tA\tC\t7.3",
            "X\t1\tA\tC\t7.3",
            "1\t2\tA\tC\t7.3",
        ], parser=parsers.standard_gwas_parser, skip_rows=1)

        with pytest.raises(val_exc.ValidationException):
            validators.standard_gwas_validator._validate_contents(reader)

    def test_positions_not_sorted(self):
        reader = readers.IterableReader([
            "#chrom\tpos\tref\talt\tpvalue",
            "1\t2\tA\tC\t7.3",
            "1\t1\tA\tC\t7.3",
            "X\t1\tA\tC\t7.3",
        ], parser=parsers.standard_gwas_parser, skip_rows=1)

        with pytest.raises(val_exc.ValidationException):
            validators.standard_gwas_validator._validate_contents(reader)

    def test_validates_for_file(self):
        sample_fn = os.path.join(os.path.dirname(__file__), 'fixtures/gwas.tab')
        is_valid = validators.standard_gwas_validator.validate(sample_fn, {  # Parser options for sample file
            'chr_col': 1,
            'pos_col': 2,
            'ref_col': 3,
            'alt_col': 4,
            'pval_col': 5,
            'is_log_pval': False
        })
        assert is_valid
