{% extends "admin/base_site.html" %}
{% load i18n static log admin_filters %}

{% block coltype %}colMS{% endblock %}
{% block bodyclass %}{{ block.super }} dashboard{% endblock %}
{% block nav-breadcrumbs %}{% endblock %}
{% block nav-sidebar %}{% endblock %}
{% block content_title %}{% endblock %}

{% block content %}
<div class="cf-dashboard">

    <div class="cf-dash-head">
        <div>
            <span class="cf-eyebrow"><i class="bi bi-grid-1x2"></i> Control Center</span>
            <h1>Good day, {% firstof user.get_short_name user.get_username %} <i class="bi bi-emoji-smile" style="color: var(--cf-accent);"></i></h1>
            <p class="cf-dash-subtitle">
                Manage accounts, campaigns, donations, and platform content from one polished dashboard.
            </p>
        </div>
        <div class="cf-quick-actions">
            <a class="cf-btn cf-btn-add" href="{% url 'admin:projects_project_changelist' %}"><i class="bi bi-rocket-takeoff"></i> Campaigns</a>
            <a class="cf-btn cf-btn-change" href="{% url 'admin:projects_donation_changelist' %}"><i class="bi bi-heart-fill"></i> Donations</a>
        </div>
    </div>

    <div class="cf-dash-grid">

        <!-- ===================== LEFT : Apps / Models ===================== -->
        <div class="cf-main">
            {% for app in app_list %}
            <section class="cf-app-card">
                <header class="cf-app-head">
                    <span class="cf-app-icon">
                        {% if app.app_label == "accounts" %}<i class="bi bi-person-badge"></i>
                        {% elif app.app_label == "auth" %}<i class="bi bi-shield-lock"></i>
                        {% elif app.app_label == "projects" %}<i class="bi bi-rocket-takeoff"></i>
                        {% elif app.app_label == "sites" %}<i class="bi bi-globe2"></i>
                        {% elif app.app_label == "taggit" %}<i class="bi bi-tags"></i>
                        {% elif app.app_label == "socialaccount" %}<i class="bi bi-people-fill"></i>
                        {% else %}<i class="bi bi-box"></i>{% endif %}
                    </span>
                    <div>
                        <h2>{{ app.name }}</h2>
                        <span class="cf-app-meta">{{ app.models|length }} model{{ app.models|pluralize }}</span>
                    </div>
                    <a class="cf-app-link" href="{{ app.app_url }}">{% translate 'Open app' %} <i class="bi bi-arrow-right"></i></a>
                </header>

                <ul class="cf-model-list">
                    {% for model in app.models %}
                    <li class="cf-model-row">
                        <div class="cf-model-info">
                        <span class="cf-model-icon">
                            {% if model.object_name == "CustomUser" %}<i class="bi bi-person-circle"></i>
                            {% elif model.object_name == "Group" %}<i class="bi bi-people-fill"></i>
                            {% elif model.object_name == "Permission" %}<i class="bi bi-shield-check"></i>
                            {% elif model.object_name == "Category" %}<i class="bi bi-folder2-open"></i>
                            {% elif model.object_name == "Project" %}<i class="bi bi-rocket-takeoff"></i>
                            {% elif model.object_name == "ProjectImage" %}<i class="bi bi-image"></i>
                            {% elif model.object_name == "Donation" %}<i class="bi bi-heart-fill"></i>
                            {% elif model.object_name == "Comment" %}<i class="bi bi-chat-left-text"></i>
                            {% elif model.object_name == "Rating" %}<i class="bi bi-star-fill"></i>
                            {% elif model.object_name == "Report" %}<i class="bi bi-flag-fill"></i>
                            {% elif model.object_name == "Site" %}<i class="bi bi-globe2"></i>
                            {% elif model.object_name == "Tag" %}<i class="bi bi-tag-fill"></i>
                            {% elif model.object_name == "EmailAddress" %}<i class="bi bi-envelope-fill"></i>
                            {% elif model.object_name == "EmailConfirmation" %}<i class="bi bi-envelope-check"></i>
                            {% elif model.object_name == "SocialAccount" %}<i class="bi bi-person-lines-fill"></i>
                            {% elif model.object_name == "SocialApp" %}<i class="bi bi-app-indicator"></i>
                            {% elif model.object_name == "SocialToken" %}<i class="bi bi-key-fill"></i>
                            {% else %}<i class="bi bi-database"></i>{% endif %}
                        </span>

                        <div class="cf-model-meta">
                            {% if model.admin_url %}
                            <a class="cf-model-name" href="{{ model.admin_url }}">{{ model.name }}</a>
                            {% else %}
                            <span class="cf-model-name">{{ model.name }}</span>
                            {% endif %}
                        </div>
                        </div>

                        <div class="cf-model-actions">
                            {% if model.add_url %}
                            <a class="cf-btn cf-btn-add" href="{{ model.add_url }}"><i class="bi bi-plus-lg"></i> {% translate 'Add' %}</a>
                            {% endif %}
                            {% if model.admin_url %}
                                {% if model.view_only %}
                                <a class="cf-btn cf-btn-view" href="{{ model.admin_url }}"><i class="bi bi-eye"></i> {% translate 'View' %}</a>
                                {% else %}
                                <a class="cf-btn cf-btn-change" href="{{ model.admin_url }}"><i class="bi bi-pencil-square"></i> {% translate 'Change' %}</a>
                                {% endif %}
                            {% endif %}
                        </div>
                    </li>
                    {% endfor %}
                </ul>
            </section>
            {% empty %}
            <div class="cf-empty">
                <i class="bi bi-shield-lock" style="font-size: 2rem; display: block; margin-bottom: 10px;"></i>
                You don't have permission to view or edit anything.
            </div>
            {% endfor %}
        </div>

        <!-- ===================== RIGHT : Recent Actions ===================== -->
        <aside class="cf-side">
            <div class="cf-recent-card">
                <header class="cf-recent-head">
                    <span class="cf-recent-icon"><i class="bi bi-clock-history"></i></span>
                    <h3>{% translate 'Recent actions' %}</h3>
                    {% get_admin_log 10 as admin_log for_user user %}
                    <span class="cf-badge">{{ admin_log|length }}</span>
                </header>
                <p class="cf-recent-sub">{% translate 'My actions' %}</p>

                {% if not admin_log %}
                <p class="cf-none"><i class="bi bi-inbox"></i><br>None available.</p>
                {% else %}
                <ol class="cf-timeline">
                    {% for entry in admin_log %}
                    <li class="cf-timeline-item
                        {% if entry.is_addition %}cf-tl-add{% elif entry.is_change %}cf-tl-change{% elif entry.is_deletion %}cf-tl-delete{% else %}cf-tl-other{% endif %}">
                        <span class="cf-tl-badge">
                            {% if entry.is_addition %}<i class="bi bi-plus-circle-fill"></i>
                            {% elif entry.is_change %}<i class="bi bi-pencil-square"></i>
                            {% elif entry.is_deletion %}<i class="bi bi-trash3-fill"></i>
                            {% else %}<i class="bi bi-dot"></i>{% endif %}
                        </span>
                        <div>
                            <p class="cf-tl-text">
                                {% if entry.is_deletion or not entry.get_admin_url %}
                                    {{ entry.object_repr|to_object_display_value }}
                                {% else %}
                                    <a href="{{ entry.get_admin_url }}">{{ entry.object_repr|to_object_display_value }}</a>
                                {% endif %}
                            </p>
                            <div class="cf-tl-meta">
                                {% if entry.content_type %}
                                <span class="cf-tl-type-item">{% filter capfirst %}{{ entry.content_type.name }}{% endfilter %}</span>
                                {% endif %}
                                {% if entry.is_addition %}
                                <span class="cf-tl-type-item" style="background:#e2f8ee;color:#17a06a;">{% translate 'Added' %}</span>
                                {% elif entry.is_change %}
                                <span class="cf-tl-type-item" style="background:#fff1e6;color:var(--cf-accent);">{% translate 'Updated' %}</span>
                                {% elif entry.is_deletion %}
                                <span class="cf-tl-type-item" style="background:#fde4e4;color:#d3312f;">{% translate 'Deleted' %}</span>
                                {% endif %}
                                <time class="cf-tl-time">{{ entry.action_time|date:"M d, Y" }} &middot; {{ entry.action_time|date:"H:i" }}</time>
                            </div>
                        </div>
                    </li>
                    {% endfor %}
                </ol>
                {% endif %}
            </div>
        </aside>

    </div>
</div>
{% endblock %}