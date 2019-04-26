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

    It expects a parsed row of data (namedtuple as output by zorp)
    """
    # Field names selected to match original portaldev api server
    chromosome = drf_serializers.CharField(source='chrom', read_only=True)
    position = drf_serializers.IntegerField(source='pos', read_only=True)
    ref_allele = drf_serializers.CharField(source='ref', read_only=True)
    alt_allele = drf_serializers.CharField(source='alt', read_only=True)
    log_pvalue = drf_serializers.FloatField(source='neg_log_pvalue', read_only=True)
    variant = drf_serializers.CharField(source='marker', read_only=True)

