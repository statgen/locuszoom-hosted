import os
import typing as ty

from django.conf import settings
from django_filters import rest_framework as filters
from rest_framework import exceptions as drf_exceptions
from rest_framework import permissions as drf_permissions
from rest_framework import generics
from rest_framework import renderers as drf_renderers

from locuszoom_plotting_service.gwas import models as lz_models

from zorp.readers import TabixReader
from zorp.parsers import standard_gwas_parser

from . import (
    permissions,
    serializers
)

from locuszoom_plotting_service.gwas import models


class GwasFilter(filters.FilterSet):
    """Filters used for GWAS endpoints, including a special "only my studies" alias"""
    me = filters.BooleanFilter(method='filter_by_user',
                               label='Show only records owned by the current logged-in user, as filter[me]')

    class Meta:
        model = models.AnalysisInfo
        fields = {
            'pmid': ('isnull', 'iexact')
        }

    def filter_by_user(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(owner=self.request.user)
        return queryset


class GwasListView(generics.ListAPIView):
    """
    List all known uploaded GWAS analyses that are available for viewing
        (public data sets, plus any private to just this user)

    This excludes any datasets that are not yet ready for viewing (eg, failed the upload step)
    """
    queryset = lz_models.AnalysisInfo.objects.filter(files__isnull=False).select_related('owner')
    serializer_class = serializers.GwasSerializer
    permission_classes = (permissions.GwasPermission,)
    ordering = ('-created',)

    filterset_class = GwasFilter
    search_fields = ('label', 'pmid')  # TODO: Future search fields: author, phenotype name, snomed code

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

    queryset = lz_models.AnalysisInfo.objects.all().select_related('owner')
    serializer_class = serializers.GwasSerializerUnprocessed
    permissions = (drf_permissions.IsAuthenticated, permissions.GwasPermission)
    ordering = ('-created',)

    def get_queryset(self):
        queryset = super(GwasListViewUnprocessed, self).get_queryset()
        return queryset.filter(owner=self.request.user)


class GwasDetailView(generics.RetrieveAPIView):
    """Metadata describing one particular uploaded GWAS"""
    permission_classes = (permissions.GwasPermission,)
    queryset = lz_models.AnalysisInfo.objects.filter(files__isnull=False)
    serializer_class = serializers.GwasSerializer


class GwasRegionView(generics.RetrieveAPIView):
    """
    Fetch the parsed GWAS data (such as from a file) for a specific region
    # TODO: Improve serialization, error handling, etc. (better follow JSONAPI spec for errors)
    """
    renderer_classes = [drf_renderers.JSONRenderer]
    filter_backends: list = []
    queryset = lz_models.AnalysisInfo.objects.filter(files__isnull=False)
    serializer_class = serializers.GwasFileSerializer
    permission_classes = (permissions.GwasPermission,)

    lookup_field = 'slug'

    def get_serializer(self, *args, **kwargs):
        """Unique scenario: a single model that returns a list of records"""
        return super(GwasRegionView, self).get_serializer(*args, many=True, **kwargs)

    def get_object(self):
        gwas = super(GwasRegionView, self).get_object()  # External-facing GWAS id given as slug in url
        chrom, start, end = self._query_params()

        if not os.path.isfile(gwas.files.normalized_gwas_path):
            raise drf_exceptions.NotFound

        reader = TabixReader(gwas.files.normalized_gwas_path, parser=standard_gwas_parser)
        return list(reader.fetch(chrom, start, end))

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
            raise drf_exceptions.ParseError(f'Cannot handle requested region size. Max allowed is {500_000}')

        return chrom, start, end
