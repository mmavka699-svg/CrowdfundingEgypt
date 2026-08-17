"""
chatbot/services.py — Native Function Calling tools for Gemini.

These functions are passed directly to the Gemini API as tools.
The LLM will automatically decide which function to call based on the user's intent.
Data is returned as structured JSON/dictionaries instead of formatted strings.
"""

from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

def get_chatbot_tools(user):
    """
    Returns a list of callable tool functions scoped to the provided user.
    These tools are injected into the Gemini API `tools` configuration.
    """

    def search_campaigns(search_terms: list[str] = None, status: str = None, category: str = None):
        """
        Search campaigns by keywords, status, or category.
        Valid statuses: 'running', 'cancelled', 'ended', 'funded', 'coming_soon'.
        """
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

        results = []
        for p in projects:
            results.append({
                "title": p.title,
                "status": p.status,
                "target": float(p.total_target),
                "raised": float(p.total_donated),
                "cat": p.category.name,
                "rating": float(p.average_rating)
            })
        return {"data": results}


    def get_platform_stats():
        """Aggregate platform-wide statistics like total projects, running projects, and total raised."""
        from projects.models import Project, Donation, Category

        total_projects = Project.objects.count()
        running_projects = Project.objects.filter(status=Project.Status.RUNNING).count()
        total_raised = Donation.objects.aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
        total_donors = Donation.objects.values("donor").distinct().count()

        categories = (
            Category.objects.annotate(
                project_count=Count("projects"),
                total_raised=Sum("projects__donations__amount"),
            )
            .order_by("-project_count")[:10]
        )

        cat_data = []
        for cat in categories:
            raised = cat.total_raised or Decimal("0.00")
            cat_data.append({
                "name": cat.name,
                "project_count": cat.project_count,
                "raised": float(raised)
            })

        return {
            "total_campaigns": total_projects,
            "running_campaigns": running_projects,
            "total_raised": float(total_raised),
            "total_donors": total_donors,
            "top_categories": cat_data
        }


    def get_my_donations():
        """Return the authenticated user's own donation history."""
        from projects.models import Donation

        if not user or not user.is_authenticated:
            return {"error": "User must log in to view donation history."}

        donations = (
            Donation.objects.filter(donor=user)
            .select_related("project")
            .order_by("-created_at")[:10]
        )

        if not donations:
            return {"message": "You haven't made any donations yet."}

        results = []
        for d in donations:
            results.append({
                "amount": float(d.amount),
                "project": d.project.title,
                "date": d.created_at.strftime('%Y-%m-%d')
            })

        return {
            "total_donated_overall": float(user.total_donations_amount),
            "recent_donations": results
        }


    def get_my_wallet():
        """Return the authenticated user's wallet balance and recent transactions."""
        from accounts.models import WalletTransaction

        if not user or not user.is_authenticated:
            return {"error": "User must log in to view wallet information."}

        transactions = (
            WalletTransaction.objects.filter(user=user)
            .order_by("-created_at")[:10]
        )
        
        tx_list = []
        for t in transactions:
            direction = "+" if t.transaction_type == WalletTransaction.TransactionType.CREDIT else "-"
            tx_list.append({
                "amount_with_direction": f"{direction}{float(t.amount)}",
                "description": t.description,
                "date": t.created_at.strftime('%Y-%m-%d')
            })

        return {
            "current_balance": float(user.wallet_balance),
            "recent_transactions": tx_list
        }


    def get_how_it_works():
        """Returns static platform usage guide (how to donate, wallet, create campaigns)."""
        return {
            "rules": [
                "Anyone can create a fundraising campaign with target and deadline.",
                "Users can donate using wallet, credit card, PayPal, Google Pay, Apple Pay.",
                "Split payments (wallet + another method) are allowed.",
                "Creators can cancel their project only if less than 25% of target is raised.",
                "Cancelled projects automatically refund all wallet donations.",
                "0% fees — 100% of donation goes to the campaign.",
                "Users can rate and comment on projects."
            ]
        }


    def get_latest_campaigns():
        """Fetch the latest running projects."""
        from projects.models import Project

        projects = Project.objects.filter(status=Project.Status.RUNNING).order_by("-created_at")[:5]
        if not projects:
            return {"error": "No running campaigns found."}
        
        results = []
        for p in projects:
            results.append({
                "title": p.title,
                "target": float(p.total_target),
                "raised": float(p.total_donated),
                "cat": p.category.name,
                "rating": float(p.average_rating)
            })
        return {"data": results}


    def get_featured_campaigns():
        """Fetch the top featured running projects."""
        from projects.models import Project

        projects = Project.objects.filter(status=Project.Status.RUNNING, is_featured=True)[:5]
        if not projects:
            return {"error": "No featured campaigns found."}
        
        results = []
        for p in projects:
            results.append({
                "title": p.title,
                "target": float(p.total_target),
                "raised": float(p.total_donated),
                "cat": p.category.name,
                "rating": float(p.average_rating)
            })
        return {"data": results}


    def get_top_rated_campaigns():
        """Fetch the top-rated running projects."""
        from projects.models import Project
        from django.db.models import Avg

        projects = (
            Project.objects.filter(status=Project.Status.RUNNING)
            .annotate(avg_rating=Avg('ratings__stars'))
            .filter(avg_rating__isnull=False)
            .order_by("-avg_rating")[:5]
        )
        if not projects:
            return {"error": "No rated campaigns found."}
        
        results = []
        for p in projects:
            results.append({
                "title": p.title,
                "rating": float(p.average_rating),
                "target": float(p.total_target),
                "raised": float(p.total_donated),
            })
        return {"data": results}


    def get_my_created_campaigns():
        """Return projects created by the authenticated user."""
        from projects.models import Project

        if not user or not user.is_authenticated:
            return {"error": "User must log in to view their created projects."}

        projects = Project.objects.filter(creator=user).order_by("-created_at")[:10]

        if not projects:
            return {"message": "You haven't created any campaigns yet."}

        results = []
        for p in projects:
            results.append({
                "title": p.title,
                "status": p.status,
                "target": float(p.total_target),
                "raised": float(p.total_donated)
            })
        return {"data": results}


    def get_project_comments(project_name: str):
        """Find a project by name and return its latest comments."""
        from projects.models import Project, Comment

        project = Project.objects.filter(title__icontains=project_name).first()

        if not project:
            return {"error": f"No matching campaign found for '{project_name}'."}

        comments = Comment.objects.filter(project=project).order_by("-created_at")[:5]

        if not comments:
            return {"message": f"The campaign '{project.title}' doesn't have any comments yet."}

        results = []
        for c in comments:
            body = c.body[:150] + ("..." if len(c.body) > 150 else "")
            results.append({
                "author": c.author.get_full_name() or c.author.email,
                "comment": body
            })
            
        return {
            "project_title": project.title,
            "recent_comments": results
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
