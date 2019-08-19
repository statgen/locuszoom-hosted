from django import forms

from . import models


class AnalysisInfoForm(forms.ModelForm):
    class Meta:
        model = models.AnalysisInfo
        fields = ('label', 'pmid', 'is_public', 'build',)


class AnalysisFilesetForm(forms.ModelForm):
    class Meta:
        model = models.AnalysisFileset
        fields = ('parser_options', 'raw_gwas_file')


class ViewLinkForm(forms.ModelForm):
    class Meta:
        model = models.ViewLink
        fields = ('label',)
