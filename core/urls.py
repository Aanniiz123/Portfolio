from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("work/", views.work, name="work"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact_view, name="contact"),
    path("api/chat/", views.chat_api, name="chat_api"),
]