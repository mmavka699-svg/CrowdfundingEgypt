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

        # Only touch RUNNING projects — cancelled ones are permanent.
        running = Project.objects.filter(status=Project.Status.RUNNING).annotate(
            total_donated_sum=Coalesce(Sum("donations__amount"), Decimal("0.00"))
        )

        # 1. Mark FUNDED: donations have reached the target
        funded_ids = list(
            running.filter(total_donated_sum__gte=F("total_target")).values_list("pk", flat=True)
        )
        funded_count = Project.objects.filter(pk__in=funded_ids).update(status=Project.Status.FUNDED)

        # 2. Mark ENDED: end_date has passed but not fully funded
        ended_count = Project.objects.filter(
            status=Project.Status.RUNNING,
            end_date__lt=today,
        ).update(status=Project.Status.ENDED)

        self.stdout.write(
            self.style.SUCCESS(
                f"sync_project_statuses: {funded_count} project(s) marked FUNDED, "
                f"{ended_count} project(s) marked ENDED."
            )
        )
