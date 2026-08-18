import json
from decimal import Decimal
from django.db.models import Q, Sum, Max, Min, Avg, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce
from projects.models import Project, Category, Donation

ALLOWED_ENTITIES = ["Project", "Category", "Donation"]

ALLOWED_FIELDS = {
    "Project": {
        "title": "char",
        "slug": "char",
        "details": "char",
        "category": "relation",
        "total_target": "numeric",
        "start_date": "date",
        "end_date": "date",
        "status": "choice",
        "is_featured": "boolean",
        "created_at": "date",
        "total_donated": "derived_numeric",
        "progress_percentage": "derived_numeric"
    },
    "Category": {
        "name": "char",
        "slug": "char",
        "description": "char"
    },
    "Donation": {
        "amount": "numeric",
        "created_at": "date"
    }
}

ALLOWED_OPERATIONS = ["list", "count", "sum", "max", "min", "avg"]

def get_project_base_queryset():
    """
    Annotate standard Project model with aggregate total_donated and progress_percentage
    so they can be filtered, ordered, or aggregated at the database level.
    """
    return Project.objects.annotate(
        total_donated_annotated=Coalesce(Sum("donations__amount"), Decimal("0.00"))
    ).annotate(
        progress_percentage_annotated=ExpressionWrapper(
            F("total_donated_annotated") * 100.0 / F("total_target"),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    )

def query_public_data(entity: str, operation: str, filters: list = None, field: str = None, ordering: str = None, limit: int = 10) -> str:
    """
    Exposes a safe, read-only database query layer. Validates all inputs to prevent SQL or ORM injection.
    
    Args:
        entity: Model to query (Project, Category, Donation).
        operation: Query operation (list, count, sum, max, min, avg).
        filters: Optional filters list of dicts: [{"field": name, "operator": op, "value": val}]
        field: Field name for aggregations.
        ordering: Optional ordering string (e.g. 'total_target' or '-created_at').
        limit: Limit parameter for list queries.
    """
    # 1. Validate Entity and Operation
    if entity not in ALLOWED_ENTITIES:
        return json.dumps({"error": f"Unauthorized or invalid entity: {entity}"})
    if operation not in ALLOWED_OPERATIONS:
        return json.dumps({"error": f"Unauthorized or invalid operation: {operation}"})

    # 2. Get base QuerySet and field mappings
    if entity == "Project":
        qs = get_project_base_queryset()
        field_mapping = {
            "title": "title",
            "slug": "slug",
            "details": "details",
            "category": "category__name",
            "total_target": "total_target",
            "start_date": "start_date",
            "end_date": "end_date",
            "status": "status",
            "is_featured": "is_featured",
            "created_at": "created_at",
            "total_donated": "total_donated_annotated",
            "progress_percentage": "progress_percentage_annotated"
        }
        model_class = Project
    elif entity == "Category":
        qs = Category.objects.all()
        field_mapping = {
            "name": "name",
            "slug": "slug",
            "description": "description"
        }
        model_class = Category
    elif entity == "Donation":
        if operation == "list":
            return json.dumps({"error": "Listing individual donations is prohibited for privacy reasons."})
        qs = Donation.objects.all()
        field_mapping = {
            "amount": "amount",
            "created_at": "created_at"
        }
        model_class = Donation

    # 3. Validate and Apply Filters
    django_filters = {}
    if filters:
        for f in filters:
            f_field = f.get("field")
            f_operator = f.get("operator", "exact")
            f_value = f.get("value")

            if f_field not in field_mapping:
                return json.dumps({"error": f"Filter field '{f_field}' is not allowed or invalid."})

            if f_operator not in ["exact", "icontains", "gt", "gte", "lt", "lte"]:
                return json.dumps({"error": f"Filter operator '{f_operator}' is invalid."})

            # Safe normalization of project status
            if entity == "Project" and f_field == "status" and isinstance(f_value, str):
                val_clean = f_value.lower().strip().replace("-", " ").replace("_", " ")
                if val_clean in ["running", "active", "currently running"]:
                    f_value = "running"
                elif val_clean in ["coming soon", "coming_soon", "upcoming", "upcoming projects", "projects starting soon", "comingsoon"]:
                    f_value = "coming_soon"
                elif val_clean in ["funded", "fully funded", "funded projects"]:
                    f_value = "funded"
                elif val_clean in ["ended", "ended projects"]:
                    f_value = "ended"
                elif val_clean in ["cancelled", "cancelled projects"]:
                    f_value = "cancelled"
                else:
                    return json.dumps({"error": f"Invalid status filter value: {f_value}"})

            orm_field = field_mapping[f_field]
            if f_operator == "exact":
                lookup = orm_field
            else:
                lookup = f"{orm_field}__{f_operator}"

            django_filters[lookup] = f_value

        try:
            qs = qs.filter(**django_filters)
        except Exception as err:
            return json.dumps({"error": f"Invalid filter values supplied: {str(err)}"})

    # 4. Execute the Query
    try:
        # Aggregation Logic
        if operation in ["sum", "max", "min", "avg"]:
            if not field:
                return json.dumps({"error": f"Field parameter is required for operation '{operation}'"})
            if field not in field_mapping:
                return json.dumps({"error": f"Field '{field}' is invalid or unauthorized."})

            orm_field = field_mapping[field]
            is_numeric = field in ["total_target", "total_donated", "progress_percentage", "amount"]
            if not is_numeric:
                return json.dumps({"error": f"Field '{field}' is not numeric and cannot be aggregated."})

            if operation == "sum":
                agg_result = qs.aggregate(result=Sum(orm_field))
            elif operation == "max":
                agg_result = qs.aggregate(result=Max(orm_field))
            elif operation == "min":
                agg_result = qs.aggregate(result=Min(orm_field))
            elif operation == "avg":
                agg_result = qs.aggregate(result=Avg(orm_field))

            val = agg_result["result"]
            if isinstance(val, Decimal):
                val = float(val)
            return json.dumps({"operation": operation, "entity": entity, "field": field, "value": val if val is not None else 0})

        elif operation == "count":
            count_val = qs.count()
            return json.dumps({"operation": "count", "entity": entity, "value": count_val})

        elif operation == "list":
            if ordering:
                is_desc = ordering.startswith("-")
                clean_order_field = ordering.lstrip("-")
                if clean_order_field not in field_mapping:
                    return json.dumps({"error": f"Invalid ordering field: {clean_order_field}"})
                orm_order_field = field_mapping[clean_order_field]
                order_expr = f"-{orm_order_field}" if is_desc else orm_order_field
                qs = qs.order_by(order_expr)
            else:
                if entity == "Project":
                    qs = qs.order_by("-created_at")

            # Apply safe limit range [1, 20]
            limit = min(max(int(limit), 1), 20)
            items = qs[:limit]

            results = []
            for item in items:
                row = {}
                for f_name, orm_name in field_mapping.items():
                    if f_name == "total_donated" and entity == "Project":
                        row[f_name] = float(item.total_donated_annotated)
                    elif f_name == "progress_percentage" and entity == "Project":
                        row[f_name] = float(item.progress_percentage_annotated)
                    elif f_name == "category" and entity == "Project":
                        row[f_name] = item.category.name if item.category else ""
                    else:
                        val = getattr(item, orm_name)
                        if isinstance(val, Decimal):
                            val = float(val)
                        elif not isinstance(val, (str, int, float, bool, type(None))):
                            val = str(val)
                        row[f_name] = val
                results.append(row)
            return json.dumps(results)

    except Exception as e:
        return json.dumps({"error": f"An error occurred during query execution: {str(e)}"})

# Private User Functions (Securely scoped to request.user session)
def get_my_wallet(user) -> str:
    if not user or not user.is_authenticated:
        return json.dumps({"error": "User is not authenticated."})
    return json.dumps({
        "wallet_balance": f"{user.wallet_balance:,.2f} EGP"
    })

def get_my_donations(user) -> str:
    if not user or not user.is_authenticated:
        return json.dumps({"error": "User is not authenticated."})
        
    donations = Donation.objects.filter(donor=user).select_related("project")
    if not donations.exists():
        return json.dumps({"message": "You have not made any donations yet."})
        
    results = []
    for d in donations:
        results.append({
            "project_title": d.project.title,
            "project_slug": d.project.slug,
            "amount": f"{d.amount:,.2f} EGP",
            "date": d.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return json.dumps(results)
