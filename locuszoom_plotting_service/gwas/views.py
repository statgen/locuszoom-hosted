"""(mostly) Template-based front end views"""

import json
import os
import typing as ty

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.urls import reverse
from django.views.generic import CreateView, DetailView
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from django.shortcuts import redirect, render
from django.http import FileResponse, HttpResponseBadRequest, HttpResponseRedirect

from locuszoom_plotting_service.taskapp import tasks

from . import forms as lz_forms
from . import models as lz_models
from . import permissions as lz_permissions


class BaseFileView(View, SingleObjectMixin):
    """
    Base class that serves up a file associated with a GWAS. This centralizes the logic in one place in case we
    change the storage location in the future. Supports serving as JSON (like an API) or as download/attachment.
    """
    queryset = lz_models.AnalysisInfo.objects.filter(files__isnull=False)

    path_arg: str  # Name of a property on the GWAS fileset object that specifies where to find the desired file
    content_type: ty.Union[str, None] = None
    download_name: ty.Union[str, None] = None

    def get(self, request, *args, **kwargs):
        gwas = self.get_object()

        filename = getattr(gwas.files, self.path_arg)
        if not os.path.isfile(filename):
            return HttpResponseBadRequest(content={'error': 'File not found'})

        response = FileResponse(open(filename, 'rb'), content_type=self.content_type)
        if self.download_name:
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(self.download_name)
        return response


@login_required()
def rerun_analysis(request, pk):
    """
    FIXME: TEMPORARY debugging view
    Replace this later with something smarter, eg "rerun, and possibly replace the options in some of the fields"
    """
    metadata = lz_models.AnalysisInfo.objects.get(pk=pk)
    files = metadata.analysisfileset_set.order_by('-created').first()
    files.ingest_status = 0
    files.save()

    if request.user != metadata.owner:
        raise HttpResponseBadRequest
    transaction.on_commit(lambda: tasks.total_pipeline(files.pk).apply_async())

    return redirect(metadata)


class GwasCreate(LoginRequiredMixin, CreateView):
    """
    Upload a GWAS file.

    Note there is a bit of trickery here to accommodate creating two models (file + metadata) instead of one.
    """
    model = lz_models.AnalysisInfo
    fields = ['label', 'pmid', 'is_public', 'build']
    template_name = 'gwas/upload.html'

    def get_form_kwargs(self):
        base = super(GwasCreate, self).get_form_kwargs()
        base.pop('prefix')  # Remove a single field that doesn't play nice with this dual-form
        return base

    def get_form(self, form_class=None):
        """The template 'form' variable will contain two, count 'em two, forms"""
        base_kwargs = self.get_form_kwargs()
        return {
            'metadata': self.get_form_class()(prefix='metadata', **base_kwargs),
            'fileset': lz_forms.AnalysisFilesetForm(prefix='fileset', **base_kwargs)
        }

    def form_valid(self, form):
        """Followup action to take after verifying the form is valid"""
        metadata = form['metadata']
        fileset = form['fileset']

        metadata.instance.owner = self.request.user
        self.object = metadata.save()  # used by get_success_url

        fileset.instance.metadata = metadata.instance
        fileset.save()

        # Deliberately skip the super call, which assumes the view has only one form
        return HttpResponseRedirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        """Override parent create view, which relies on a single form.is_valid"""
        self.object = None

        form = self.get_form()
        if form['metadata'].is_valid() and form['fileset'].is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


#######
# Data/download views, including raw JSON files that don't match the API design.
class GwasSummaryStats(lz_permissions.GwasAccessPermission, BaseFileView):
    path_arg = 'normalized_gwas_path'
    content_type = 'application/gzip'
    download_name = 'summary_stats.gz'


class GwasIngestLog(lz_permissions.GwasAccessPermission, BaseFileView):
    path_arg = 'normalized_gwas_log_path'
    download_name = 'ingest_log.log'


class GwasManhattanJson(lz_permissions.GwasAccessPermission, BaseFileView):
    path_arg = 'manhattan_path'
    content_type = 'application/json'


class GwasQQJson(lz_permissions.GwasAccessPermission, BaseFileView):
    path_arg = 'qq_path'
    content_type = 'application/json'


#######
# HTML views
class GwasSummary(lz_permissions.GwasAccessPermission, DetailView):
    """
    Basic GWAS overview. Shows manhattan plot and other summary info for a dataset.
    """
    template_name = 'gwas/gwas_summary.html'
    # Some studies will still be processing- it's still ok to see the summary page for these
    queryset = lz_models.AnalysisInfo.objects.select_related('files')
    context_object_name = 'gwas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gwas = self.get_object()
        context['js_vars'] = json.dumps({
            'ingest_status': gwas.ingest_status,
            'manhattan_url': reverse('gwas:manhattan-json', kwargs={'pk': gwas.pk}) if gwas.files else None,
            'qq_url': reverse('gwas:qq-json', kwargs={'pk': gwas.pk}) if gwas.files else None,
        })
        return context


class GwasLocus(lz_permissions.GwasAccessPermission, DetailView):
    """
    A LocusZoom plot associated with one specific GWAS region

    The region is actually specified as query params; if none are provided, it defaults to the top hit in the study
    """
    template_name = 'gwas/gwas_region.html'
    queryset = lz_models.AnalysisInfo.objects.filter(files__isnull=False)
    context_object_name = 'gwas'

    def get_context_data(self, **kwargs):
        """Additional template context"""
        context = super().get_context_data(**kwargs)
        gwas = self.get_object()

        context['js_vars'] = json.dumps({
            'assoc_base_url': reverse('apiv1:gwas-region', kwargs={'pk': gwas.pk}),
            'label': gwas.label,
            'build': gwas.build,
            # Default region for bare URLs is the top hit in the study
            'chr': gwas.top_hit_view.chrom,
            'start': gwas.top_hit_view.start,
            'end': gwas.top_hit_view.end,
        })
        return context
