import os

import pytest

from util.ingest import loaders
from util.zorp import readers


class TestFileFormatDetection:
    def test_handles_text_files(self):
        text_fn = os.path.join(os.path.dirname(__file__), 'fixtures/sample.tab')
        reader = loaders.make_reader(text_fn)
        assert isinstance(reader, readers.TextFileReader)

    def test_handles_gzip_files(self):
        text_fn = os.path.join(os.path.dirname(__file__), 'fixtures/sample.tab.gz')
        reader = loaders.make_reader(text_fn)
        assert isinstance(reader, readers.TabixReader)

    def test_fails(self):
        text_fn = os.path.join(os.path.dirname(__file__), 'fixtures/sample.tar')
        with pytest.raises(Exception):
            reader = loaders.make_reader(text_fn)
            assert isinstance(reader, readers.TextFileReader)
