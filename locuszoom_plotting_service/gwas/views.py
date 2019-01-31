from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView
from django.views.generic.edit import CreateView

from django.shortcuts import get_object_or_404, render
from django.http import FileResponse

from . import models as lz_models


def home(request):
    return render(request,  'gwas/home.html')


class GwasCreate(CreateView):
    model = lz_models.Gwas
    fields = ['analysis', 'build', 'imputed', 'file_location']
    template_name = 'gwas/upload.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


@login_required
def gwas_manhattan_json(request, pk):
    """Return the JSON file that internally stores manhattan plot data"""
    # TODO: Convert this to an API endpoint in the future
    gwas = get_object_or_404(lz_models.Gwas, pk=pk)
    response = FileResponse(open(gwas.manhattan_fn, 'rb'))
    response['Content-Type'] = 'application/json'
    return response


class GwasSummary(DetailView):
    """
    Basic GWAS view. Used to view one specific analysis from one specific dataset

    In the future this might become, say, a manhattan plot with a detail view link (in line with PheWeb)
    """
    template_name = 'gwas/gwas_summary.html'
    queryset = lz_models.Gwas.objects.all()


class GwasLocus(DetailView):
    """
    A LocusZoom plot associated with the GWAS

    In the future this might become, say, a manhattan plot with a detail view link (in line with PheWeb)
    """
    template_name = 'gwas/gwas_locus.html'
    queryset = lz_models.Gwas.objects.all()
