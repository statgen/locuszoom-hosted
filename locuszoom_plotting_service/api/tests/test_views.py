from django.urls import reverse
from rest_framework.test import APITestCase

from locuszoom_plotting_service.gwas.tests.factories import (
    AnalysisFilesetFactory,
    AnalysisInfoFactory,
    UserFactory,
    ViewLinkFactory,
)


class TestListview(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_owner = user1 = UserFactory()
        cls.user_other = user2 = UserFactory()

        # Create fake studies with no data, that will render anyway
        cls.study_private = AnalysisInfoFactory(owner=user1, is_public=False,
                                                files=AnalysisFilesetFactory(has_completed=True))
        cls.study_public = AnalysisInfoFactory(owner=user2, is_public=True,
                                               files=AnalysisFilesetFactory(has_completed=True))

    def tearDown(self):
        self.client.logout()

    def test_deleted_studies_not_accessible(self):
        study_public = AnalysisInfoFactory(is_public=True)
        study_public.delete()
        response = self.client.get(reverse('apiv1:gwas-list'))
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(payload['data']), 1)

        record_ids = [item['id'] for item in payload['data']]
        self.assertNotIn(study_public.slug, record_ids)

    ###
    # Permissions-related tests
    def test_owner_can_see_private_study(self):
        self.client.force_login(self.user_owner)
        response = self.client.get(reverse('apiv1:gwas-list'))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['data']), 2)

    def test_other_user_cannot_see_private_study(self):
        self.client.force_login(self.user_other)
        response = self.client.get(reverse('apiv1:gwas-list'))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['data']), 1)

    def test_without_auth_shows_only_public(self):
        response = self.client.get(reverse('apiv1:gwas-list'))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['data']), 1)

    def test_filter_special_me(self):
        # Special filter syntax excludes studies by any other user, even if they are public and otherwise visible
        self.client.force_login(self.user_owner)
        response = self.client.get(reverse('apiv1:gwas-list'), {'filter[me]': True})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['data']), 1)


class TestDetailView(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_owner = user1 = UserFactory()
        cls.user_other = user2 = UserFactory()

        # Create fake studies with no data, that will render anyway
        cls.study_private = AnalysisInfoFactory(owner=user1, is_public=False,
                                                files=AnalysisFilesetFactory(has_completed=True))
        cls.study_public = AnalysisInfoFactory(owner=user2, is_public=True,
                                               files=AnalysisFilesetFactory(has_completed=True))

        cls.study_private_viewlink = ViewLinkFactory(gwas=cls.study_private)

    def test_renders_slug_instead_of_id(self):
        # This test exists to catch regressions from a package that handles ID field badly
        response = self.client.get(reverse('apiv1:gwas-metadata', args=[self.study_public.slug]))
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['data']['id'], self.study_public.slug, 'Exposes slug, not ID')

    def test_deleted_studies_not_accessible(self):
        study_public = AnalysisInfoFactory(is_public=True)
        study_public.delete()
        response = self.client.get(reverse('apiv1:gwas-metadata', args=[study_public.slug]))
        self.assertEqual(response.status_code, 404)

    ###
    # Permissions-related tests
    def test_other_user_cannot_see_private_study(self):
        self.client.force_login(self.user_other)
        response = self.client.get(reverse('apiv1:gwas-metadata', args=[self.study_private.slug]))
        self.assertEqual(response.status_code, 403)

    def test_other_user_can_see_private_study_via_shareable_link(self):
        self.client.force_login(self.user_other)
        response = self.client.get(reverse('apiv1:gwas-metadata', args=[self.study_private.slug]),
                                   {'token': self.study_private_viewlink.code})
        self.assertEqual(response.status_code, 200)

    def test_private_study_can_be_accessed_via_shareable_link(self):
        response = self.client.get(reverse('apiv1:gwas-metadata', args=[self.study_private.slug]),
                                   {'token': self.study_private_viewlink.code})
        print(response.content)
        self.assertEqual(response.status_code, 200)
