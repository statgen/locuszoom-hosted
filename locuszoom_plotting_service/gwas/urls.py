from django.urls import path
from django.contrib.auth.decorators import login_required

from django.views.generic import RedirectView

from . import views

app_name = 'gwas'
urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', login_required(views.GwasCreate.as_view()), name='upload'),

    # Dataset-specific views
    path('gwas/', RedirectView.as_view(pattern_name='home')),
    path('gwas/<pk>/', views.GwasSummary.as_view(), name='overview'),
    path('gwas/<pk>/region/', views.GwasLocus.as_view(), name='region'),

    # Temporary debugging views
    path('gwas/<pk>/rerun/', views.rerun_analysis, name='rerun'),

    # Some views that serve up raw data from server
    path('gwas/<pk>/data/', views.GwasSummaryStats.as_view(), name='gwas-download'),
    path('gwas/<pk>/data/ingest_log/', views.GwasIngestLog.as_view(), name='gwas-ingest-log'),
    path('gwas/<pk>/data/manhattan/', views.GwasManhattanJson.as_view(), name='manhattan-json'),
    path('gwas/<pk>/data/qq/', views.GwasQQJson.as_view(), name='qq-json'),

]
