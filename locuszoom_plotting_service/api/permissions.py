from rest_framework.permissions import BasePermission

from locuszoom_plotting_service.gwas.models import AnalysisInfo


class GwasPermission(BasePermission):
    """The request user is allowed access to the given GWAS study"""
    def has_object_permission(self, request, view, obj: AnalysisInfo):
        return obj.can_view(request.user)
