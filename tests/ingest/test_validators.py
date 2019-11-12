import os

import pytest

from util.ingest import (
    exceptions as val_exc, validators
)

from zorp import (
    parsers, sniffers
)


class TestStandardGwasValidator:
    def test_valid_input(self):
        reader = sniffers.guess_gwas_generic([
            "#chrom\tpos\tref\talt\tneg_log_pvalue",
            "1\t1\tA\tC\t7.3",
            "X\t1\tA\tC\t7.3",
        ], skip_rows=1)

        is_valid = validators.standard_gwas_validator._validate_contents(reader)
        assert is_valid

    @pytest.mark.skip(reason="Unclear whether this is actually a requirement for PheWeb loaders; revisit")
    def test_wrong_chrom_order(self):
        reader = sniffers.guess_gwas_generic([
            "#chrom\tpos\tref\talt\tneg_log_pvalue",
            "2\t1\tA\tC\t7.3",
            "1\t1\tA\tC\t7.3"
        ], skip_rows=1)

        with pytest.raises(val_exc.ValidationException):
            validators.standard_gwas_validator._validate_contents(reader)

    def test_chroms_not_contiguous(self):
        reader = sniffers.guess_gwas_generic([
            "#chrom\tpos\tref\talt\tneg_log_pvalue",
            "1\t1\tA\tC\t7.3",
            "X\t1\tA\tC\t7.3",
            "1\t2\tA\tC\t7.3",
        ], skip_rows=1)

        with pytest.raises(val_exc.ValidationException):
            validators.standard_gwas_validator._validate_contents(reader)

    def test_positions_not_sorted(self):
        reader = sniffers.guess_gwas_generic([
            "#chrom\tpos\tref\talt\tneg_log_pvalue",
            "1\t2\tA\tC\t7.3",
            "1\t1\tA\tC\t7.3",
            "X\t1\tA\tC\t7.3",
        ])

        with pytest.raises(val_exc.ValidationException):
            validators.standard_gwas_validator._validate_contents(reader)

    def test_validates_for_file(self):
        sample_fn = os.path.join(os.path.dirname(__file__), 'fixtures/gwas.tab')
        parser = parsers.GenericGwasLineParser(**{  # Parser options for sample file
            'chrom_col': 1,
            'pos_col': 2,
            'ref_col': 3,
            'alt_col': 4,
            'pvalue_col': 5,
            'is_neg_log_pvalue': False
        })
        reader = sniffers.guess_gwas_generic(sample_fn, parser=parser)
        is_valid = validators.standard_gwas_validator.validate(sample_fn, reader)
        assert is_valid
