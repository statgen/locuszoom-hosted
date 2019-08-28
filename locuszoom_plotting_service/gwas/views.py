"""(mostly) Template-based front end views"""

import json
import logging
import os
import shutil
import typing as ty

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
)
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from django.shortcuts import redirect
from django.http import (
    FileResponse,
    Http404,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)

from locuszoom_plotting_service.taskapp import tasks

from . import forms as lz_forms
from . import models as lz_models
from . import permissions as lz_permissions
from .templatetags.shared import add_token
from . import util


logger = logging.getLogger(__name__)


class BaseFileView(View, SingleObjectMixin):
    """
    Base class that serves up a file associated with a GWAS. This centralizes the logic in one place in case we
    change the storage location in the future. Supports serving as JSON (like an API) or as download/attachment.
    """
    queryset = lz_models.AnalysisInfo.objects.ingested()

    path_arg: str  # Name of a property on the GWAS fileset object that specifies where to find the desired file
    content_type: ty.Union[str, None] = None
    download_name: ty.Union[str, None] = None

    def get(self, request, *args, **kwargs):
        gwas = self.get_object()
        target = gwas.files or gwas.most_recent_upload

        filename = getattr(target, self.path_arg)
        if not os.path.isfile(filename):
            return HttpResponseBadRequest(content={'error': 'File not found'})

        response = FileResponse(open(filename, 'rb'), content_type=self.content_type)
        if self.download_name:
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(self.download_name)
        return response


@login_required()
def rerun_analysis(request, slug):
    """
    FIXME: TEMPORARY debugging view
    Replace this later with something smarter, eg "rerun, and possibly replace the options in some of the fields"
    """
    metadata = lz_models.AnalysisInfo.objects.all_active().get(slug=slug)
    files = metadata.analysisfileset_set.order_by('-created').first()
    files.ingest_status = 0
    files.save()

    if request.user != metadata.owner:
        raise HttpResponseBadRequest
    transaction.on_commit(lambda: tasks.total_pipeline(files.pk).apply_async())

    return redirect(metadata)


#######
# Data/download views, including raw JSON files that don't match the API design.
class GwasSummaryStats(lz_permissions.GwasViewPermission, BaseFileView):
    path_arg = 'normalized_gwas_path'
    content_type = 'application/gzip'
    download_name = 'summary_stats.gz'


class GwasIngestLog(lz_permissions.GwasViewPermission, BaseFileView):
    queryset = lz_models.AnalysisInfo.objects.all_active()  # Allow viewing logs of a file that failed ingest
    path_arg = 'normalized_gwas_log_path'
    download_name = 'ingest_log.log'


class GwasManhattanJson(lz_permissions.GwasViewPermission, BaseFileView):
    path_arg = 'manhattan_path'
    content_type = 'application/json'


class GwasQQJson(lz_permissions.GwasViewPermission, BaseFileView):
    path_arg = 'qq_path'
    content_type = 'application/json'


#######
# HTML views
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
        # State stored on instance attr: Make sure it gets wiped before every new request
        self.object = None

        form = self.get_form()
        if form['metadata'].is_valid() and form['fileset'].is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class GwasEdit(lz_permissions.GwasOwner, UpdateView):
    """Metadata editing UI. In the future, this may also incorporate a button to change analysis parameters
        and/or rerun data ingestion. (eg, to get new code/features)"""
    model = lz_models.AnalysisInfo
    context_object_name = "gwas"
    form_class = lz_forms.AnalysisInfoForm
    template_name = "gwas/edit.html"


class GwasDelete(lz_permissions.GwasOwner, DeleteView):
    """Show a confirmation page and delete the study if applicable"""
    queryset = lz_models.AnalysisInfo.objects.all_active()
    context_object_name = "gwas"
    template_name = "gwas/delete.html"

    success_url = reverse_lazy('home')

    def delete(self, request, *args, **kwargs):
        """
        Clean up the local files, then, if that succeeds, mark the DB record as deleted
        We do things in this order so as not to retain data that the user thought was deleted
        """
        gwas = self.get_object()
        # The same gwas file might be revised or re-processed, and we want to delete all known copies.
        for fileset in gwas.analysisfileset_set.all():
            target_path = util.get_study_folder(fileset, absolute_path=True)
            logger.info('User has requested that we delete media folder: ', target_path)
            if not target_path or not os.path.isdir(target_path) or \
                target_path.strip('/') == settings.MEDIA_ROOT.strip('/'):
                # Guard against some malformed path bugs that would be really awkward to explain
                raise Exception('Cannot find the data requested for deletion')

            shutil.rmtree(target_path)
        return super(GwasDelete, self).delete(request, *args, **kwargs)


class GwasRegion(lz_permissions.GwasViewPermission, DetailView):
    """
    A LocusZoom plot associated with one specific GWAS region

    The region is actually specified as query params; if none are provided, it defaults to the top hit in the study
    """
    template_name = 'gwas/gwas_region.html'
    queryset = lz_models.AnalysisInfo.objects.ingested()
    context_object_name = 'gwas'

    def get_context_data(self, **kwargs):
        """Additional template context"""
        context = super().get_context_data(**kwargs)
        gwas = self.get_object()

        token = self.request.GET.get('token')
        context['token'] = token
        context['js_vars'] = json.dumps({
            'assoc_base_url': add_token(
                reverse('apiv1:gwas-region', kwargs={'slug': gwas.slug}),
                token
            ),
            'label': gwas.label,
            'build': gwas.build,
            # Default region for bare URLs is the top hit in the study
            'chr': gwas.top_hit_view.chrom,
            'start': gwas.top_hit_view.start,
            'end': gwas.top_hit_view.end,
        })
        return context


class GwasShare(LoginRequiredMixin, CreateView):
    """
    Sharing options for a study. Only the owner can see this page.

    The permissions check is implemented in `dispatch` (because the model for this view is different than the model
        returned by `get_object` FIXME: This is a bit weird.
    """
    model = lz_models.ViewLink
    form_class = lz_forms.ViewLinkForm

    context_object_name = "link"
    template_name = "gwas/share.html"

    # Fields required because of wonky permissions on this view
    permission_denied_message = 'You must be the author of this study to access this page.'
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        # FIXME: This is ugly: it performs a permissions check on a different model, so can't use the existing
        #   permissions class
        gwas = get_object_or_404(lz_models.AnalysisInfo, slug=self.kwargs['slug'])
        if not (gwas.owner == request.user) or gwas.is_removed:
            return self.handle_no_permission()
        return super(GwasShare, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gwas = get_object_or_404(lz_models.AnalysisInfo, slug=self.kwargs['slug'])
        context['gwas'] = gwas
        context['viewlinks'] = gwas.viewlink_set.all()
        return context

    def form_valid(self, form):
        """Set a relationship field for the specified GWAS"""
        # The form doesn't specify the target directly; that gets referenced in the URL
        # As such, if this block triggers an error then something has gone quite far wrong
        gwas = self.kwargs.get('slug')
        if not gwas:
            raise Http404
        form.instance.gwas = get_object_or_404(lz_models.AnalysisInfo, slug=gwas)
        return super().form_valid(form)


class GwasSummary(lz_permissions.GwasViewPermission, DetailView):
    """
    Basic GWAS overview. Shows manhattan plot and other summary info for a dataset.
    """
    template_name = 'gwas/gwas_summary.html'
    # Some studies will still be processing- it's still ok to see the summary page for these
    queryset = lz_models.AnalysisInfo.objects.all_active().select_related('files')
    context_object_name = 'gwas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gwas = self.get_object()

        token = self.request.GET.get('token')  # If there is a secret access link, add that token to all API URLs
        context['token'] = token
        context['js_vars'] = json.dumps({
            'ingest_status': gwas.ingest_status,
            'region_url': add_token(
                reverse('gwas:region', kwargs= {'slug': gwas.slug}),
                token
            ),
            'manhattan_url': add_token(
                reverse('gwas:manhattan-json', kwargs={'slug': gwas.slug}),
                token,
            ) if gwas.files else None,
            'qq_url': add_token(
                reverse('gwas:qq-json', kwargs={'slug': gwas.slug}),
                token,
            ) if gwas.files else None,
        })
        return context
