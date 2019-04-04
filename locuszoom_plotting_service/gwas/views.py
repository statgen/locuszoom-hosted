"""(mostly) Template-based front end views"""

import os
import typing as ty

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView

from django.shortcuts import render
from django.http import FileResponse, HttpResponseBadRequest

from . import models as lz_models
from . import permissions as lz_permissions


class BaseFileView(View, SingleObjectMixin):
    """
    Base class that serves up a file associated with a GWAS. This centralizes the logic in one place in case we
    change the storage location in the future. Supports serving as JSON (like an API) or as download/attachment.
    """
    queryset = lz_models.Gwas.objects.all()

    path_arg: str
    content_type: ty.Union[str, None] = None
    download_name: ty.Union[str, None] = None

    def get(self, request, *args, **kwargs):
        gwas = self.get_object()

        filename = getattr(gwas, self.path_arg)
        if not os.path.isfile(filename):
            return HttpResponseBadRequest(content={'error': 'File not found'})

        response = FileResponse(open(filename, 'rb'), content_type=self.content_type)
        if self.download_name:
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(self.download_name)
        return response


@login_required()
def home(request):
    return render(request,  'gwas/home.html')


class GwasCreate(LoginRequiredMixin, CreateView):
    """Render a simple HTML form"""
    model = lz_models.Gwas
    fields = ['analysis', 'is_public', 'build', 'imputed', 'n_cases', 'n_controls', 'raw_gwas_file']
    template_name = 'gwas/upload.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(GwasCreate, self).form_valid(form)


#######
# Data/download views, including raw JSON files that don't match the API design.
class GwasSummaryStats(LoginRequiredMixin, lz_permissions.GwasAccessPermission, BaseFileView):
    path_arg = 'normalized_gwas_path'
    content_type = 'application/gzip'
    download_name = 'summary_stats.gz'


class GwasIngestLog(LoginRequiredMixin, lz_permissions.GwasAccessPermission, BaseFileView):
    path_arg = 'normalized_gwas_log_path'
    download_name = 'ingest_log.log'


class GwasManhattanJson(LoginRequiredMixin, lz_permissions.GwasAccessPermission, BaseFileView):
    path_arg = 'manhattan_path'
    content_type = 'application/json'


class GwasQQJson(LoginRequiredMixin, lz_permissions.GwasAccessPermission, BaseFileView):
    path_arg = 'qq_path'
    content_type = 'application/json'


#######
# HTML views
class GwasSummary(LoginRequiredMixin, lz_permissions.GwasAccessPermission, DetailView):
    """
    Basic GWAS overview. Shows manhattan plot and other summary info for a dataset.
    """
    template_name = 'gwas/gwas_summary.html'
    queryset = lz_models.Gwas.objects.all()


class GwasLocus(LoginRequiredMixin, lz_permissions.GwasAccessPermission, DetailView):
    """
    A LocusZoom plot associated with one specific GWAS region

    The region is actually specified as query params; we will need a mechanism to define a "Default region"
    for bare URLs (TODO)
    """
    template_name = 'gwas/gwas_region.html'
    queryset = lz_models.Gwas.objects.all()  # TODO: Consider filtering queryset (eg eliminate deleted etc)

    def get_context_data(self, **kwargs):
        """Additional template context"""
        context = super().get_context_data(**kwargs)
        gwas = self.get_object()

        import json # TODO: proper template handling
        context['js_vars'] = json.dumps({
            'assoc_base_url': reverse('apiv1:gwas-region', kwargs={'pk': gwas.id}),
            'label': gwas.analysis,
            'build': gwas.build,
            # TODO- future: provide sane default values for chr, start, and end position (if user hits url without a region selected)

        })
        return context
