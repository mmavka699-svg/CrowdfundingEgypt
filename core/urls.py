from django.urls import path , include
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("about/", views.about_view, name="about"),
    path("verification/", views.verification_view, name="verification"),
    path("fees/", views.fees_view, name="fees"),
    path("refund/", views.refund_view, name="refund"),
    path("report/", views.report_view, name="report"),
    path("api/", include("chatbot.urls")),    
]
