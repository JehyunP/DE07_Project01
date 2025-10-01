from django.urls import path
from . import views


app_name = 'backends'
urlpatterns = [
    path('',views.index, name='index'),
    path('<int:program_id>/', views.detail, name='detail'),
]