# third_party/tests.py
# ------------------------------------------------------------
# One-file test suite for the third_party app
# Run: python manage.py test third_party
# ------------------------------------------------------------
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from third_party.models import VendorRequest
from workflow.enums import WorkflowStates


class VendorRequestEndToEndTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user", password="pass")
        self.staff = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )
        self.obj = VendorRequest.objects.create(name="Acme", description="Demo")

    def test_model_defaults_and_str(self):
        obj = VendorRequest.objects.create(name="WidgetCo")
        self.assertEqual(obj.state, WorkflowStates.DRAFT)
        self.assertIn("WidgetCo", str(obj))

    def test_list_and_detail_require_login_then_render(self):
        list_url = reverse("third_party:request_list")
        detail_url = reverse("third_party:request_detail", args=[self.obj.pk])

        # Unauthenticated → redirect to login
        resp = self.client.get(list_url)
        self.assertEqual(resp.status_code, 302)

        # Authenticated → OK
        self.client.login(username="user", password="pass")
        resp = self.client.get(list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Vendor Requests")

        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.obj.name)

    def test_submit_via_htmx_transitions_to_review(self):
        self.client.login(username="user", password="pass")
        url = reverse("third_party:request_submit", args=[self.obj.pk])

        resp = self.client.post(url, **{"HTTP_HX-Request": "true"})
        self.assertEqual(resp.status_code, 200)
        self.obj.refresh_from_db()
        self.assertEqual(self.obj.state, WorkflowStates.REVIEW)
        self.assertContains(resp, 'id="workflow-actions"')  # fragment updated

    def test_nonstaff_cannot_approve(self):
        # move to review
        self.client.login(username="user", password="pass")
        self.client.post(reverse("third_party:request_submit", args=[self.obj.pk]))
        self.client.logout()

        self.client.login(username="user", password="pass")
        url = reverse("third_party:request_approve", args=[self.obj.pk])
        resp = self.client.post(url, **{"HTTP_HX-Request": "true"})
        self.assertEqual(resp.status_code, 403)
        self.obj.refresh_from_db()
        self.assertEqual(self.obj.state, WorkflowStates.REVIEW)

    def test_staff_can_approve(self):
        # move to review
        self.client.login(username="user", password="pass")
        self.client.post(reverse("third_party:request_submit", args=[self.obj.pk]))
        self.client.logout()

        # approve as staff
        self.client.login(username="staff", password="pass")
        url = reverse("third_party:request_approve", args=[self.obj.pk])
        resp = self.client.post(url, **{"HTTP_HX-Request": "true"})
        self.assertEqual(resp.status_code, 200)
        self.obj.refresh_from_db()
        self.assertEqual(self.obj.state, WorkflowStates.APPROVED)

    def test_staff_can_reject(self):
        # move to review
        self.client.login(username="user", password="pass")
        self.client.post(reverse("third_party:request_submit", args=[self.obj.pk]))
        self.client.logout()

        self.client.login(username="staff", password="pass")
        url = reverse("third_party:request_reject", args=[self.obj.pk])
        resp = self.client.post(url)  # HTMX or normal both fine
        self.assertIn(resp.status_code, (200, 302))
        self.obj.refresh_from_db()
        self.assertEqual(self.obj.state, WorkflowStates.REJECTED)
