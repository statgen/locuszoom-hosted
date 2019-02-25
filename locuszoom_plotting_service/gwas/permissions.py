"""
Implement permissions restrictions as decorators
"""
from django.contrib.auth.mixins import UserPassesTestMixin


class GwasAccessPermission(UserPassesTestMixin):
    """Check that the request user is allowed to see the requested study"""
    raise_exception = True
    permission_denied_message = 'You do not have permission to view the requested resource.'

    def test_func(self):
        model = self.get_object()
        return model.can_view(self.request.user)

