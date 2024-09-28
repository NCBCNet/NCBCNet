from django.contrib import admin
from django.urls import path

from server import views

app_name = "server"
urlpatterns = [
    path('', views.index, name='index'),
]
