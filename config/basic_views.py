"""
Simple top level views not tied to specific data
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "pages/home.html"


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "pages/profile.html"

    def get_context_data(self, **kwargs):
        return {'user': self.request.user}
