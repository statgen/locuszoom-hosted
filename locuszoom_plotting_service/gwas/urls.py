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
    path('gwas/<pk>/manhattan', views.gwas_manhattan_json, name='manhattan-json'),  # JSON endpoint; move to API?
    path('gwas/<pk>/region/', views.GwasLocus.as_view(), name='region'),
]


