"""
Minor hack:

We use Django allauth for sign-in, but want to limit functionality to social signin *only*.
This file declares a set of custom routes that hides local-account functionality (like password reset) that would
otherwise be available to users of this addon.

https://stackoverflow.com/a/41454423/1422268
"""

import importlib

from django.conf.urls import include, url
from django.urls import path

from allauth.account.views import login, logout, SignupView
from allauth.socialaccount import providers
from allauth.socialaccount import views as social_views

providers_urlpatterns = []

for provider in providers.registry.get_list():
    prov_mod = importlib.import_module(provider.get_package() + '.urls')
    providers_urlpatterns += getattr(prov_mod, 'urlpatterns', [])

urlpatterns = [
    path('', include(providers_urlpatterns)),  # Provider-specific callbacks (eg /accounts/google/login/)
    path('social/connections/', social_views.ConnectionsView.as_view(), name='socialaccount_connections'),
    # url(r'^confirm-email/(?P<key>[-:\w]+)/$', confirm_email, name='account_confirm_email'),
    path("login/", login, name='account_login'),
    path('logout/', logout, name='account_logout'),
    path('signup/', SignupView.as_view(), name='account_signup'),
    path('social/signup/', social_views.SignupView.as_view(), name='socialaccount_signup'),
]
