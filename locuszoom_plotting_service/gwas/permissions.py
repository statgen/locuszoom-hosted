"""
Implement permissions restrictions as decorators
"""
from django.contrib.auth.mixins import UserPassesTestMixin


class GwasViewPermission(UserPassesTestMixin):
    """Check that the request user is allowed to see the requested study"""
    raise_exception = True
    permission_denied_message = 'You do not have permission to view the requested resource.'

    def test_func(self):
        model = self.get_object()
        return model.can_view(self.request.user)


class GwasOwner(UserPassesTestMixin):
    raise_exception = True
    permission_denied_message = 'You must be the author of this study to access this page.'

    def test_func(self):
        model = self.get_object()
        return model.owner == self.request.user
