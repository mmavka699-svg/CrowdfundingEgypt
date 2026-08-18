"""
chatbot/services.py — Minified Native Function Calling tools for Gemini.
"""

from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

def get_chatbot_tools(user):
    """Returns callable tool functions scoped to the user."""

    def search_campaigns(search_terms: list[str] = None, status: str = None, category: str = None):
        """Search projects by keyword, status(running/cancelled/ended/funded/coming_soon), or category."""
        from projects.models import Project

        projects = Project.objects.all()

        if status:
            projects = projects.filter(status=status)
        elif not search_terms and not category:
            projects = projects.filter(status=Project.Status.RUNNING)

        if category:
            projects = projects.filter(category__name__icontains=category)

        if search_terms:
            q = Q()
            for term in search_terms[:3]:
                q |= Q(title__icontains=term) | Q(details__icontains=term) | Q(category__name__icontains=term)
            projects = projects.filter(q)
            
        projects = projects.distinct()[:5]

        if not projects:
            return {"error": "No campaigns found."}

        return {"data": [
            {
                "title": p.title,
                "status": p.status,
                "target": int(p.total_target),
                "raised": int(p.total_donated),
                "cat": p.category.name,
                "rate": float(p.average_rating)
            } for p in projects
        ]}


    def get_platform_stats():
        """Get platform totals: projects, raised, donors, top categories, and all available categories list."""
        from projects.models import Project, Donation, Category

        total_projects = Project.objects.count()
        running_projects = Project.objects.filter(status=Project.Status.RUNNING).count()
        total_raised = Donation.objects.aggregate(s=Sum("amount"))["s"] or Decimal("0")
        total_donors = Donation.objects.values("donor").distinct().count()

        categories = Category.objects.annotate(
            project_count=Count("projects"),
            total_raised=Sum("projects__donations__amount"),
        ).order_by("-project_count")
        
        all_cats = [c.name for c in categories]

        cat_data = []
        for cat in categories[:10]:
            cat_data.append({
                "n": cat.name,
                "c": cat.project_count,
                "r": int(cat.total_raised or 0)
            })

        return {
            "total_camp": total_projects,
            "running_camp": running_projects,
            "raised": int(total_raised),
            "donors": total_donors,
            "top_cats": cat_data,
            "all_cats": all_cats
        }


    def get_my_donations():
        """Get authenticated user's donations."""
        from projects.models import Donation

        if not user or not user.is_authenticated:
            return {"error": "Login required"}

        donations = Donation.objects.filter(donor=user).select_related("project").order_by("-created_at")[:10]

        if not donations:
            return {"message": "No donations"}

        return {
            "total": int(user.total_donations_amount),
            "recent": [{"amt": int(d.amount), "proj": d.project.title, "date": d.created_at.strftime('%Y-%m-%d')} for d in donations]
        }


    def get_my_wallet():
        """Get user's wallet balance and transactions."""
        from accounts.models import WalletTransaction

        if not user or not user.is_authenticated:
            return {"error": "Login required"}

        transactions = WalletTransaction.objects.filter(user=user).order_by("-created_at")[:10]
        
        return {
            "bal": int(user.wallet_balance),
            "txs": [{"amt": f"{'+' if t.transaction_type == 'credit' else '-'}{int(t.amount)}", "desc": t.description} for t in transactions]
        }


    def get_how_it_works():
        """Get platform rules (donate, wallet, create, register, profile, rate, report)."""
        return {
            "rules": [
                "Register: Click 'Sign Up', enter details.",
                "Profile: Edit picture, country, password from settings.",
                "Create: Anyone can start a campaign with a target/deadline.",
                "Donate: Use wallet, card, PayPal, Google/Apple Pay.",
                "Cancel: Creators can cancel if <25% target raised. Refunds go to wallet.",
                "Fees: 0% taken, 100% goes to campaign.",
                "Interact: Users can comment, rate (1-5 stars), or report spam/fraud on campaigns."
            ]
        }


    def get_latest_campaigns():
        """Get 5 newest running projects."""
        from projects.models import Project

        projects = Project.objects.filter(status=Project.Status.RUNNING).order_by("-created_at")[:5]
        if not projects:
            return {"error": "None found"}
        
        return {"data": [{"title": p.title, "target": int(p.total_target), "raised": int(p.total_donated), "cat": p.category.name} for p in projects]}


    def get_featured_campaigns():
        """Get 5 featured running projects."""
        from projects.models import Project

        projects = Project.objects.filter(status=Project.Status.RUNNING, is_featured=True)[:5]
        if not projects:
            return {"error": "None found"}
        
        return {"data": [{"title": p.title, "target": int(p.total_target), "raised": int(p.total_donated), "cat": p.category.name} for p in projects]}


    def get_top_rated_campaigns():
        """Get 5 top-rated running projects."""
        from projects.models import Project
        from django.db.models import Avg

        projects = Project.objects.filter(status=Project.Status.RUNNING).annotate(avg_rating=Avg('ratings__stars')).filter(avg_rating__isnull=False).order_by("-avg_rating")[:5]
        if not projects:
            return {"error": "None found"}
        
        return {"data": [{"title": p.title, "rate": float(p.average_rating), "raised": int(p.total_donated)} for p in projects]}


    def get_my_created_campaigns():
        """Get user's created projects."""
        from projects.models import Project

        if not user or not user.is_authenticated:
            return {"error": "Login required"}

        projects = Project.objects.filter(creator=user).order_by("-created_at")[:10]

        if not projects:
            return {"message": "None"}

        return {"data": [{"title": p.title, "status": p.status, "target": int(p.total_target), "raised": int(p.total_donated)} for p in projects]}


    def get_project_comments(project_name: str):
        """Get recent comments for a specific project name."""
        from projects.models import Project, Comment

        project = Project.objects.filter(title__icontains=project_name).first()

        if not project:
            return {"error": "Not found"}

        comments = Comment.objects.filter(project=project).order_by("-created_at")[:5]

        if not comments:
            return {"message": "No comments"}

        return {
            "title": project.title,
            "cmts": [{"author": c.author.get_short_name() or "User", "text": c.body[:100]} for c in comments]
        }

    return [
        search_campaigns,
        get_platform_stats,
        get_my_donations,
        get_my_wallet,
        get_latest_campaigns,
        get_featured_campaigns,
        get_top_rated_campaigns,
        get_my_created_campaigns,
        get_project_comments,
        get_how_it_works
    ]
