from django.urls import path
from . import views


app_name = 'backends'
urlpatterns = [
    path('',views.index, name='index'),
    path('<int:program_id>/', views.detail, name='detail'),
    path("genre/<str:half_year>/", views.genre_distribution, name="genre_distribution"),
    path("api/subgenre/<int:genre_id>/<str:half_year>/", views.subgenre_distribution_api, name="subgenre_distribution_api"),
    path("subgenre/<int:subgenre_id>/<str:half_year>/", views.subgenre_programs, name="subgenre_programs"),
    path('genreTrend/', views.genreTrend, name='genreTrend'),
    path('genreDetail/', views.genreDetail, name='genreDetail'),
    path('ottplatformTrend/', views.ottplatformTrend, name='ottplatformTrend'),
    path('rating_views/', views.rating_views, name='rating_views'),
]