from rest_framework.permissions import BasePermission

from locuszoom_plotting_service.gwas.models import Gwas

######
# Eventually, write real permissions classes

# class IsPublicGwas(BasePermission):
#     def has_object_permission(self, request, view, obj: Gwas) -> bool:
#         return obj.is_public
#
#
# class IsOwner(BasePermission):
#     def has_object_permission(self, request, view, obj: Gwas) -> bool:
#         return request.user == obj.owner


class GwasPermission(BasePermission):
    """The request user is allowed access to the given GWAS study"""
    def has_object_permission(self, request, view, obj: Gwas):
        return obj.can_view(request.user)
