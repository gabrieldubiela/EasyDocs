# D:\Gabriel\Programs\EasyDocs\easydocs\urls.py

from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('users/logout/', views.logout_view, name='users-logout'),
    path('files/', include('files.urls')),
]
