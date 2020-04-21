import os

from zorp import parsers, sniffers

from util.ingest import processors


# A sample file with enough data to be worth meaningfully processing
SAMPLE_FILE = os.path.join(os.path.dirname(__file__), 'fixtures/gwas.tab')
# A sample file, processed into the standardized internal representation
SAMPLE_NORM = os.path.join(os.path.dirname(__file__), 'fixtures/gwas.tab.gz')


class TestPipelineTasks:
    def test_normalizes(self, tmpdir):
        parser_options = {  # Parser options for sample file
                'chrom_col': 1,
                'pos_col': 2,
                'ref_col': 3,
                'alt_col': 4,
                'pvalue_col': 5,
                'is_neg_log_pvalue': False
        }
        parser = parsers.GenericGwasLineParser(**parser_options)
        reader = sniffers.guess_gwas_generic(SAMPLE_FILE, parser=parser, skip_errors=True)

        status = processors.normalize_contents(
            reader,
            os.path.join(tmpdir, 'normalized.txt'),
            'GRCh38',
            debug_mode=True
        )

        assert status is True, 'Normalization completed successfully'
        assert os.path.isfile(os.path.join(tmpdir, 'normalized.txt.gz')), 'Normalized file written'
        assert os.path.isfile(os.path.join(tmpdir, 'normalized.txt.gz.tbi')), 'Normalized file was tabix indexed'

    def test_makes_manhattan(self, tmpdir):
        expected = tmpdir / 'manhattan.json'
        status = processors.generate_manhattan('GRCh38', SAMPLE_NORM, expected)
        assert status is True
        assert expected.exists(), 'Manhattan data created'

    def test_makes_qq(self, tmpdir):
        expected = os.path.join(tmpdir, 'qq.json')
        status = processors.generate_qq(SAMPLE_NORM, expected)
        assert status is True
        assert os.path.isfile(expected), 'QQ data created'
