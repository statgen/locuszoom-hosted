import os
import typing as ty

from django.conf import settings
from rest_framework import exceptions as drf_exceptions
from rest_framework import permissions as drf_permissions
from rest_framework import generics
from rest_framework import renderers as drf_renderers

from locuszoom_plotting_service.api.filters import GwasFilter
from locuszoom_plotting_service.gwas import models as lz_models

from zorp.sniffers import guess_gwas_standard

from . import (
    permissions,
    serializers
)


class GwasListView(generics.ListAPIView):
    """
    List all known uploaded GWAS analyses that are available for viewing
        (public data sets, plus any private to just this user)

    This excludes any datasets that are not yet ready for viewing (eg, failed the upload step)
    """
    queryset = lz_models.AnalysisInfo.objects.ingested().select_related('owner')
    serializer_class = serializers.GwasSerializer
    permission_classes = (permissions.GwasViewPermission,)
    # Show oldest first, so that people see high quality examples on the homepage. (eventually we could curate)
    ordering = ('created',)

    filterset_class = GwasFilter
    search_fields = ('label', 'study_name', 'pmid')

    def get_queryset(self):
        queryset = super(GwasListView, self).get_queryset()
        modified = queryset.filter(is_public=True)
        if self.request.user.is_authenticated:
            modified |= queryset.filter(owner=self.request.user)
        return modified


class GwasListViewUnprocessed(generics.ListAPIView):
    """
    List all GWAS studies owned by a specific user, *including* those that are pending or failed ingest
    """
    schema = None  # This is a private endpoint for internal use; hide from documentation

    queryset = lz_models.AnalysisInfo.objects.all_active().select_related('owner')
    serializer_class = serializers.GwasSerializerUnprocessed
    permissions = (drf_permissions.IsAuthenticated, permissions.GwasViewPermission)
    ordering = ('-created',)

    def get_queryset(self):
        queryset = super(GwasListViewUnprocessed, self).get_queryset()
        return queryset.filter(owner=self.request.user)


class GwasDetailView(generics.RetrieveAPIView):
    """Metadata describing one particular uploaded GWAS"""
    permission_classes = (permissions.GwasViewPermission,)
    queryset = lz_models.AnalysisInfo.objects.ingested()
    serializer_class = serializers.GwasSerializer

    lookup_field = 'slug'


class GwasRegionView(generics.RetrieveAPIView):
    """
    Fetch the parsed GWAS data (such as from a file) for a specific region

    This is not a JSONAPI endpoint and it does not draw from a database. Therefore, it is intentionally allowed to use
        a different (more concise) format and disables default query param validation/ filtering behavior
    """
    renderer_classes = [drf_renderers.JSONRenderer]
    filter_backends: list = []
    queryset = lz_models.AnalysisInfo.objects.ingested()
    serializer_class = serializers.GwasFileSerializer
    permission_classes = (permissions.GwasViewPermission,)

    lookup_field = 'slug'

    def get_serializer(self, *args, **kwargs):
        """Unique scenario: a single model that returns a list of records"""
        return super(GwasRegionView, self).get_serializer(*args, many=True, **kwargs)

    def get_object(self):
        gwas = super(GwasRegionView, self).get_object()  # External-facing GWAS id given as slug in url
        chrom, start, end = self._query_params()

        if not os.path.isfile(gwas.files.normalized_gwas_path):
            raise drf_exceptions.NotFound

        # We deliberately exclude missing pvalues because this endpoint is primarily aimed at association plots
        reader = guess_gwas_standard(gwas.files.normalized_gwas_path)\
            .add_filter('neg_log_pvalue')

        try:
            return list(reader.fetch(chrom, start, end))
        except ValueError:
            # PySAM will throw a ValueError when tabixing to a chrom not present in the file (but it's ok with an
            #   empty region in a known chromosome)
            # Let's make the behavior the same: no known chromosome = no data for region
            return []

    def _query_params(self) -> ty.Tuple[str, int, int]:
        """
        Specific rules for GWAS retrieval
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
            start = int(start)
            end = int(end)
        except ValueError:
            raise drf_exceptions.ParseError('"start" and "end" must be integers')

        if end <= start:
            raise drf_exceptions.ParseError('"end" position must be greater than "start"')

        if not (0 <= (end - start) <= settings.LZ_MAX_REGION_SIZE):
            raise drf_exceptions.ParseError(
                f'Cannot handle requested region size. Max allowed is {settings.LZ_MAX_REGION_SIZE}')

        return chrom, start, end
