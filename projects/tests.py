from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import CustomUser
from projects.models import Project, Category


class AutocompleteSearchTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="creator@example.com",
            password="Password123!",
            first_name="Creator",
            last_name="User",
            mobile_phone="01012345678",
            is_active=True,
        )
        self.category = Category.objects.create(name="Technology", slug="technology")
        self.project = Project.objects.create(
            creator=self.user,
            title="Smart Solar Energy System",
            details="Solar energy project details.",
            category=self.category,
            total_target=Decimal("50000.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timezone.timedelta(days=30),
            status=Project.Status.RUNNING,
        )
        self.project.tags.add("solar", "tech")

    def test_autocomplete_endpoint(self):
        url = reverse("projects:autocomplete")
        response = self.client.get(url, {"q": "Solar"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        self.assertIn("tags", data)
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["title"], "Smart Solar Energy System")

    def test_autocomplete_empty_query(self):
        url = reverse("projects:autocomplete")
        response = self.client.get(url, {"q": ""})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["results"], [])
        self.assertEqual(data["tags"], [])


class CompactMoneyFormatTest(TestCase):
    def test_compact_money_filter(self):
        from projects.templatetags.project_tags import compact_money
        self.assertEqual(compact_money(2500000), "2.5M")
        self.assertEqual(compact_money(1000000), "1M")
        self.assertEqual(compact_money(1250000), "1.25M")
        self.assertEqual(compact_money(500000), "500,000")

    def test_project_formatted_target_property(self):
        user = CustomUser.objects.create_user(
            email="creator2@example.com",
            password="Password123!",
            first_name="Creator2",
            last_name="User2",
            mobile_phone="01012345679",
            is_active=True,
        )
        category = Category.objects.create(name="Health", slug="health")
        project = Project.objects.create(
            creator=user,
            title="Hospital Project",
            details="Medical project details.",
            category=category,
            total_target=Decimal("2500000.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timezone.timedelta(days=30),
            status=Project.Status.RUNNING,
        )
        self.assertEqual(project.formatted_target, "2.5M EGP")
