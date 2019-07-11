"""
Serialize data representing GWAS studies
"""
import math

from rest_framework import serializers as drf_serializers

from locuszoom_plotting_service.gwas import models as lz_models


class GwasSerializer(drf_serializers.ModelSerializer):
    owner_name = drf_serializers.SerializerMethodField(source='get_owner_name', read_only=True)
    url = drf_serializers.CharField(source='get_absolute_url', read_only=True)

    def get_owner_name(self, obj):
        return obj.owner.display_name

    class Meta:
        model = lz_models.AnalysisInfo
        fields = ['id', 'created', 'label', 'build', 'url', 'owner_name']


class GwasFileSerializer(drf_serializers.Serializer):
    """
    This is a read-only serializer, and cannot be used with, eg, upload views

    It operates on a file, not a model. It expects a parsed row of data (namedtuple as output by zorp)
    """
    # Field names selected to match original portaldev api server
    chromosome = drf_serializers.CharField(source='chrom', read_only=True)
    position = drf_serializers.IntegerField(source='pos', read_only=True)
    ref_allele = drf_serializers.CharField(source='ref', read_only=True)
    alt_allele = drf_serializers.CharField(source='alt', read_only=True)
    log_pvalue = drf_serializers.SerializerMethodField(method_name='get_neg_log_pvalue', read_only=True)
    variant = drf_serializers.CharField(source='marker', read_only=True)

    def get_neg_log_pvalue(self, row):
        """
        Many GWAS programs suffer from underflow and may represent small p=0/-logp=inf

        The JSON standard can't handle "Infinity", but the string 'Infinity' can be type-coerced by JS, eg +value
        Therefore we serialize this as a special case so it can be used in the frontend
        """
        value = row.neg_log_pvalue
        if math.isinf(value):
            return 'Infinity'
        else:
            return value

