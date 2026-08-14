from django.urls import path , include
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("about/", views.about_view, name="about"),
    path("api/", include("chatbot.urls")),    
]
