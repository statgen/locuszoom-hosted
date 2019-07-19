from django.urls import path
from django.contrib.auth.decorators import login_required

from django.views.generic import RedirectView

from . import views

app_name = 'gwas'
urlpatterns = [
    path('upload/', login_required(views.GwasCreate.as_view()), name='upload'),

    # Dataset-specific views
    path('', RedirectView.as_view(pattern_name='home')),
    path('<pk>/', views.GwasSummary.as_view(), name='overview'),
    path('<pk>/region/', views.GwasLocus.as_view(), name='region'),

    # Temporary debugging views
    path('<pk>/rerun/', views.rerun_analysis, name='rerun'),

    # Some views that serve up raw data from server
    path('<pk>/data/', views.GwasSummaryStats.as_view(), name='gwas-download'),
    path('<pk>/data/ingest_log/', views.GwasIngestLog.as_view(), name='gwas-ingest-log'),
    path('<pk>/data/manhattan/', views.GwasManhattanJson.as_view(), name='manhattan-json'),
    path('<pk>/data/qq/', views.GwasQQJson.as_view(), name='qq-json'),
]
