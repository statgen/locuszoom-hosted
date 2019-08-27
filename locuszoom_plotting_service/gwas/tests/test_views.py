from django.test import TestCase
from django.urls import reverse


from .factories import (
    UserFactory, AnalysisInfoFactory, ViewLinkFactory
)


class TestOverviewPermissions(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_owner = user1 = UserFactory()
        cls.user_other = user2 = UserFactory()

        # Create fake studies with no data, that will render anyway
        cls.study_private = AnalysisInfoFactory(owner=user1, is_public=False)
        cls.study_public = AnalysisInfoFactory(owner=user2, is_public=True)

        cls.study_private_viewlink = ViewLinkFactory(gwas=cls.study_private)

    def tearDown(self):
        self.client.logout()

    # Logged-in permissions
    def test_owner_can_see_private_study(self):
        self.client.force_login(self.user_owner)

        response = self.client.get(reverse('gwas:overview', args=[self.study_private.slug]))
        self.assertContains(response, 'still being processed', status_code=200,
                            msg_prefix='User should be able to see their own study')

        response = self.client.get(reverse('gwas:overview', args=[self.study_public.slug]))
        self.assertContains(response, 'still being processed', status_code=200,
                            msg_prefix='Public study should be visible')

    def test_other_user_cannot_see_private_study(self):
        self.client.force_login(self.user_other)
        response = self.client.get(reverse('gwas:overview', args=[self.study_private.slug]))
        self.assertNotContains(response, 'still being processed', status_code=403,
                               msg_prefix='Private study should not be visible')

    def test_other_user_can_see_private_study_via_shareable_link(self):
        self.client.force_login(self.user_other)
        response = self.client.get(self.study_private_viewlink.get_absolute_url())
        self.assertNotContains(response, 'edit', status_code=200,
                               msg_prefix='Other users can see, but not edit, a private study via share link')

    # Logged-out permissions
    def test_public_study_no_auth_required(self):
        response = self.client.get(reverse('gwas:overview', args=[self.study_public.slug]))
        self.assertEqual(response.status_code, 200)

    def test_private_study_requires_auth(self):
        response = self.client.get(reverse('gwas:overview', args=[self.study_private.slug]))
        self.assertEqual(response.status_code, 403, 'User must be logged in')

        self.client.force_login(self.user_other)
        response = self.client.get(reverse('gwas:overview', args=[self.study_private.slug]))
        self.assertEqual(response.status_code, 403, 'Only owner can see a private study')

    # Things that do not depend on whether user is logged in
    def test_private_study_can_be_accessed_via_shareable_link(self):
        response = self.client.get(self.study_private_viewlink.get_absolute_url())
        self.assertContains(response,
                            f'token={self.study_private_viewlink.code}',
                            status_code=200,
                            msg_prefix='The token is appended to other links within the page')

    def test_multiple_private_links_can_exist_for_a_single_study(self):
        second_link = ViewLinkFactory(gwas=self.study_private)

        response = self.client.get(second_link.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_share_links_are_specific_to_a_study(self):
        other_link = ViewLinkFactory(gwas=self.study_public)
        response = self.client.get(self.study_private.get_absolute_url(token=other_link.code))
        self.assertEqual(response.status_code, 403)

    def test_fake_share_links_are_rejected(self):
        response = self.client.get(self.study_private.get_absolute_url(token='fjord'))
        self.assertEqual(response.status_code, 403)
