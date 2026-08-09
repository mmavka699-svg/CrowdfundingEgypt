from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import CustomUser
from projects.models import Project, Category, Donation, Rating


class HomeViewDynamicStatsTest(TestCase):
    def setUp(self):
        self.creator = CustomUser.objects.create_user(
            email="creator@example.com",
            password="Password123!",
            first_name="Creator",
            last_name="User",
            mobile_phone="01012345678",
            is_active=True,
        )
        self.donor = CustomUser.objects.create_user(
            email="donor@example.com",
            password="Password123!",
            first_name="Donor",
            last_name="User",
            mobile_phone="01087654321",
            is_active=True,
        )
        self.category = Category.objects.create(name="Community", slug="community")
        self.project = Project.objects.create(
            creator=self.creator,
            title="Clean Water Initiative",
            details="Providing clean water to villages.",
            category=self.category,
            total_target=Decimal("20000.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timezone.timedelta(days=30),
            status=Project.Status.RUNNING,
        )
        Donation.objects.create(project=self.project, donor=self.donor, amount=Decimal("5000.00"))
        Rating.objects.create(project=self.project, user=self.donor, stars=4)

    def test_home_view_calculates_dynamic_stats(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("stats", response.context)
        stats = response.context["stats"]
        self.assertEqual(stats["total_raised"], 5000)
        self.assertEqual(stats["total_projects"], 1)
        self.assertEqual(stats["active_backers"], 1)
        self.assertEqual(stats["satisfaction_rate"], 80)
