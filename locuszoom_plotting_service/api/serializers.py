import decimal

from django.contrib.auth import get_user_model
from rest_framework import exceptions as drf_exceptions
from rest_framework import serializers as drf_serializers
import pysam

from locuszoom_plotting_service.gwas import models as lz_models


User = get_user_model()


class GwasSerializer(drf_serializers.ModelSerializer):
    url = drf_serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = lz_models.Gwas
        fields = ['id', 'analysis', 'build', 'imputed', 'url']


class GwasFileSerializer(object):
    """A customized serializer that extracts the underlying file data for an analysis"""
    def __init__(self, instance=None, **kwargs):
        self.instance = instance
        self.chrom = kwargs['context']['chrom']
        self.start = kwargs['context']['start']
        self.end = kwargs['context']['end']


    # TODO: to_representation on Serializer base class; define preset field serializers
    @property
    def data(self) -> dict:
        fn = self.instance.file_location.name
        reader = pysam.TabixFile(fn)
        if self.chrom not in reader.contigs:
            raise drf_exceptions.ValidationError('Invalid chromosome region specified')

        # The very specific sample data file has data we want as follows:
        #  chrom	pos	ref	alt	pval
        #  1	869334	G	A	0.637

        # and lz api is expected to return rows with keys [chromosome, log_pvalue, ref_allele, variant
        region = reader.fetch(self.chrom, self.start, self.end, parser=pysam.asTuple())
        data = []
        for r in region:
            try:
                parsed = {
                        'chromosome': r[0],
                        'position': int(r[1]),
                        'ref_allele': r[2],
                        'log_pvalue': -decimal.Decimal(r[4]).log10(),  # TODO: replace with locuszoom_db code - https://github.com/statgen/locuszoom-db/blob/master/locuszoom/db/loaders.py#L80
                        'variant': f'{r[0]}:{r[1]}_{r[2]}/{r[3]}'  # TODO: Phasing marker?
                    }
                data.append(parsed)
            except:
                # FIXME: How do we handle extreme pvalues on a log plot? (yields domain errors on server unless we use decimal instead of float)
                # FIXME: This is almost certainly not the ideal choice post-demo stage
                print(r)
        return {'data': data}
