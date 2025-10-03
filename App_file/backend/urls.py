from django.urls import path
from . import views


app_name = 'backends'
urlpatterns = [
    path('',views.index, name='index'),
    path('<int:program_id>/', views.detail, name='detail'),
    #path('<str:genre_name>/',views.subgenreportion, name='subgenreportion'),
    #path('genre/<str:half_year>/',views.genreportion, name='genreportion'),
    path("genre/<str:half_year>/", views.genre_distribution, name="genre_distribution"),
    path("api/subgenre/<int:genre_id>/<str:half_year>/", views.subgenre_distribution_api, name="subgenre_distribution_api"),
    path("subgenre/<int:subgenre_id>/<str:half_year>/", views.subgenre_programs, name="subgenre_programs"),
]