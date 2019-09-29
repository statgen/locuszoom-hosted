import os

from util.ingest import processors


# A sample file with enough data to be worth meaningfully processing
SAMPLE_FILE = os.path.join(os.path.dirname(__file__), 'fixtures/gwas.tab')
# A sample file, processed into the standardized internal representation
SAMPLE_NORM = os.path.join(os.path.dirname(__file__), 'fixtures/gwas.tab.gz')


class TestPipelineTasks:
    def test_normalizes(self, tmpdir):
        status = processors.normalize_contents(
            SAMPLE_FILE,
            {  # Parser options for sample file
                'chrom_col': 1,
                'pos_col': 2,
                'ref_col': 3,
                'alt_col': 4,
                'pvalue_col': 5,
                'is_neg_log_pvalue': False
            },
            os.path.join(tmpdir, 'normalized.txt'),
            os.path.join(tmpdir, 'logalog.log'),
        )

        assert status is True, 'Normalization completed successfully'
        assert os.path.isfile(os.path.join(tmpdir, 'normalized.txt.gz')), 'Normalized file written'
        assert os.path.isfile(os.path.join(tmpdir, 'normalized.txt.gz.tbi')), 'Normalized file was tabix indexed'

    def test_makes_manhattan(self, tmpdir):
        expected = tmpdir / 'manhattan.json'
        status = processors.generate_manhattan(SAMPLE_NORM, expected)
        assert status is True
        assert expected.exists(), 'Manhattan data created'

    def test_makes_qq(self, tmpdir):
        expected = os.path.join(tmpdir, 'qq.json')
        status = processors.generate_qq(SAMPLE_NORM, expected)
        assert status is True
        assert os.path.isfile(expected), 'QQ data created'
