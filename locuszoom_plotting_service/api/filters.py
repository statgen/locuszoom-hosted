import re

from django_filters import rest_framework as filters
from rest_framework_json_api.filters import QueryParameterValidationFilter

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


class ExtraQueryParameterValidationFilter(QueryParameterValidationFilter):
    """
    Our API has a special feature (shareable access tokens) that JSON API didn't plan for.

    We need to modify the default validator to allow this extra query parameter. Technically the name `token` is not
        spec compliant but it's also rather unlikely to be used. (FIXME?)
    """
    query_regex = re.compile(QueryParameterValidationFilter.query_regex.pattern + '|^(token)$')
