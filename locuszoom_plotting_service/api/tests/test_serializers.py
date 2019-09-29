import unittest

from zorp.parsers import BasicVariant

from locuszoom_plotting_service.api import serializers


class TestGwasFileSerializer(unittest.TestCase):
    def test_serializer_handles_missing_data(self):
        mock = BasicVariant('1', 2, None, 'A', 'G', None, None, None, None)
        ser = serializers.GwasFileSerializer(instance=mock).data
        self.assertIsNone(ser['log_pvalue'], 'Handles missing pvalues')
        self.assertIsNone(ser['beta'], 'Handles missing beta')
        self.assertIsNone(ser['se'], 'Handles missing sebeta')
        self.assertIsNone(ser['alt_allele_freq'], 'Handles missing alt allele freq')
