"""
Management command: sync_project_statuses

Usage:
    python manage.py sync_project_statuses

Bulk-updates the DB `status` field for every project that is still marked
"running" but should now be "ended" (past end_date) or "funded" (donations
have reached the total_target).

Run this periodically (e.g. a daily cron/Windows Task Scheduler job) to keep
statuses accurate even for projects that nobody visits.

Example cron entry (Linux):
    0 1 * * * /path/to/venv/bin/python /path/to/manage.py sync_project_statuses

Example Windows Task Scheduler action:
    Program: D:\\...\\venv\\Scripts\\python.exe
    Arguments: manage.py sync_project_statuses
    Start in: D:\\...\\CrowdfundingEgypt
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum, F, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal

from projects.models import Project


class Command(BaseCommand):
    help = "Sync DB status for all projects (ended / funded / running)."

    def handle(self, *args, **options):
        today = timezone.localdate()

        # 1. Mark COMING_SOON: start_date is in the future
        coming_soon_count = Project.objects.filter(
            status=Project.Status.RUNNING,
            start_date__gt=today,
        ).update(status=Project.Status.COMING_SOON)

        # 2. Mark RUNNING: start_date reached for coming_soon projects
        started_count = Project.objects.filter(
            status=Project.Status.COMING_SOON,
            start_date__lte=today,
            end_date__gte=today,
        ).update(status=Project.Status.RUNNING)

        # Re-evaluate target status for active candidates
        candidates = Project.objects.filter(
            status__in=[Project.Status.RUNNING, Project.Status.COMING_SOON]
        ).annotate(
            total_donated_sum=Coalesce(Sum("donations__amount"), Decimal("0.00"))
        )

        # 3. Mark FUNDED: donations have reached the target
        funded_ids = list(
            candidates.filter(total_donated_sum__gte=F("total_target")).values_list("pk", flat=True)
        )
        funded_count = Project.objects.filter(pk__in=funded_ids).update(status=Project.Status.FUNDED)

        # 4. Mark ENDED: end_date has passed but not fully funded
        ended_count = Project.objects.filter(
            status__in=[Project.Status.RUNNING, Project.Status.COMING_SOON],
            end_date__lt=today,
        ).update(status=Project.Status.ENDED)

        self.stdout.write(
            self.style.SUCCESS(
                f"sync_project_statuses: {coming_soon_count} project(s) marked COMING_SOON, "
                f"{started_count} project(s) activated to RUNNING, "
                f"{funded_count} project(s) marked FUNDED, "
                f"{ended_count} project(s) marked ENDED."
            )
        )
