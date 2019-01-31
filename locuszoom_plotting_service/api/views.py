from rest_framework import exceptions as drf_exceptions
from rest_framework import generics
from rest_framework import renderers as drf_renderers

from locuszoom_plotting_service.gwas import models as lz_models

from . import serializers


class GwasListView(generics.ListAPIView):
    """List all known uploaded GWAS analyses"""
    # TODO: No current support for file upload via API endpoint
    queryset = lz_models.Gwas.objects.all()
    serializer_class = serializers.GwasSerializer
    ordering = ('id',)


class GwasDetailView(generics.RetrieveAPIView):
    """Metadata describing one particular uploaded GWAS"""
    queryset = lz_models.Gwas.objects.filter(pipeline_complete__isnull=False).all()
    serializer_class = serializers.GwasSerializer


class GwasRegionView(generics.RetrieveAPIView):
    """
    Fetch the GWAS data (such as from a file) for a specific region
    # TODO: Improve serialization, error handling, etc. (in errors section, not detail)
    """
    renderer_classes = [drf_renderers.JSONRenderer]
    filter_backends = []
    queryset = lz_models.Gwas.objects.all()
    serializer_class = serializers.GwasFileSerializer

    def get_serializer_context(self):
        chrom, start, end = self._query_params()
        return {'chrom': chrom, 'start': start, 'end': end}

    def _query_params(self):
        """
        Specific rules for GWAS retrieval
        # TODO: Write tests!
        - Must specify chrom, start, and end as query params
        - start and end must be integers
        - end > start
        - 0 <= (end - start) <= 500000
        """
        params = self.request.query_params

        chrom = params.get('chrom', None)
        start = params.get('start', None)
        end = params.get('end', None)

        if not (chrom and start and end):
            raise drf_exceptions.ParseError('Must specify "chrom", "start", and "end" as query parameters')

        try:
            start = float(start)
            end = float(end)
        except ValueError:
            raise drf_exceptions.ParseError('"start" and "end" must be integers')

        if end <= start:
            raise drf_exceptions.ParseError('"end" position must be greater than "start"')

        if not (0 <= (end - start) <= 500_000):
            raise drf_exceptions.ParseError(f'Cannot handle requested region size. Max allowed is {500_000}')

        return chrom, start, end
