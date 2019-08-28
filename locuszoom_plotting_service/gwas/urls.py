from django.urls import path
from django.contrib.auth.decorators import login_required

from django.views.generic import RedirectView

from . import views

app_name = 'gwas'
urlpatterns = [
    path('upload/', login_required(views.GwasCreate.as_view()), name='upload'),

    # Dataset-specific views
    path('', RedirectView.as_view(pattern_name='home')),
    path('<slug>/', views.GwasSummary.as_view(), name='overview'),
    path('<slug>/delete/', views.GwasDelete.as_view(), name='delete'),
    path('<slug>/edit/', views.GwasEdit.as_view(), name='edit'),
    path('<slug>/region/', views.GwasRegion.as_view(), name='region'),
    path('<slug>/share/', views.GwasShare.as_view(), name='share'),

    # Temporary debugging views
    path('<slug>/rerun/', views.rerun_analysis, name='rerun'),

    # Some views that serve up raw data from server
    path('<slug>/data/', views.GwasSummaryStats.as_view(), name='gwas-download'),
    path('<slug>/data/ingest_log/', views.GwasIngestLog.as_view(), name='gwas-ingest-log'),
    path('<slug>/data/manhattan/', views.GwasManhattanJson.as_view(), name='manhattan-json'),
    path('<slug>/data/qq/', views.GwasQQJson.as_view(), name='qq-json'),
]
