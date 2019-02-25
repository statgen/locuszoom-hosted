"""
Serialize data representing GWAS studies
"""
import decimal

from rest_framework import serializers as drf_serializers

from locuszoom_plotting_service.gwas import models as lz_models


class GwasSerializer(drf_serializers.ModelSerializer):
    url = drf_serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = lz_models.Gwas
        fields = ['id', 'analysis', 'build', 'imputed', 'url']


class GwasFileSerializer(drf_serializers.Serializer):
    """
    This is a read-only serializer, and cannot be used with, eg, upload views

    It expects a parsed row of data
    """
    # Field names selected to match original portaldev api server
    chromosome = drf_serializers.CharField(read_only=True, source='chrom')
    position = drf_serializers.IntegerField(source='pos', read_only=True)
    ref_allele = drf_serializers.CharField(source='ref', read_only=True)
    alt_allele = drf_serializers.CharField(source='alt', read_only=True)
    log_pvalue = drf_serializers.SerializerMethodField(source='get_log_pvalue', read_only=True)
    variant = drf_serializers.SerializerMethodField(source='get_variant', read_only=True)

    def get_variant(self, row):
        return '{0}:{1}_{2}/{3}'.format(row.chrom, row.pos, row.ref, row.alt, row.pvalue)

    def get_log_pvalue(self, row):
        # TODO: revisit whether to store pvalues or logpvalues internally
        return -decimal.Decimal(row.pvalue).log10(),

