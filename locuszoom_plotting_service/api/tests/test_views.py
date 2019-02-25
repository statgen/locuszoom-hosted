from rest_framework.test import APITestCase
from django.urls import reverse


from locuszoom_plotting_service.gwas.tests.factories import (
    UserFactory, GwasFactory
)


class TestListviewPermissions(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_owner = user1 = UserFactory()
        cls.user_other = user2 = UserFactory()

        # Create fake studies with no data, that will render anyway
        cls.study_private = GwasFactory(owner=user1, is_public=False)
        cls.study_public = GwasFactory(owner=user2, is_public=True)

    def tearDown(self):
        self.client.logout()

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

    def test_api_requires_authentication(self):
        response = self.client.get(reverse('apiv1:gwas-list'))
        # TODO: should this return a 403?
        self.assertEqual(response.status_code, 403)
