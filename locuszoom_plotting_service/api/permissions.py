from rest_framework.permissions import BasePermission

from locuszoom_plotting_service.gwas.models import AnalysisInfo


class GwasViewPermission(BasePermission):
    """The current user is allowed access to the given GWAS study"""
    def has_object_permission(self, request, view, obj: AnalysisInfo):
        token = request.GET.get('token', None)
        return obj.can_view(request.user, token=token)
