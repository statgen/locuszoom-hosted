from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpRequest


class AccountAdapter(DefaultAccountAdapter):
    """Disable locally-managed accounts; only OAuth allowed. (even for development)"""
    def is_open_for_signup(self, request: HttpRequest):
        return False


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Note: a google quirk doesn't allow IPs in oauth url (even eg 0.0.0.0); use localhost instead"""
    def is_open_for_signup(self, request: HttpRequest, sociallogin: Any):
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)
