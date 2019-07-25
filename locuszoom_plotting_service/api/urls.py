"""
Routes for the raw data API
"""

from django.urls import path
from rest_framework.renderers import OpenAPIRenderer
from rest_framework.schemas import get_schema_view

from . import views

schema_view = get_schema_view(title='LocusZoom API', renderer_classes=[OpenAPIRenderer])

app_name = "api"
urlpatterns = [
    path('gwas/', views.GwasListView.as_view(), name='gwas-list'),
    path('gwas/user-all/', views.GwasListViewUnprocessed.as_view(), name='gwas-user-all'),
    path('gwas/<slug>/', views.GwasDetailView.as_view(), name='gwas-metadata'),
    path('gwas/<slug>/data/', views.GwasRegionView.as_view(), name='gwas-region'),
    # "Standardized" api schema; can be used to auto-create api clients.
    path('schema/', schema_view)
]
