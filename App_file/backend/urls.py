from django.urls import path
from . import views


app_name = 'backends'
urlpatterns = [
    path('',views.index, name='index'),
    path('<int:program_id>/', views.detail, name='detail'),
    path('genreTrend/', views.genreTrend, name='genreTrend'),
    path('genreDetail/', views.genreDetail, name='genreDetail'),
    path('ottplatformTrend/', views.ottplatformTrend, name='ottplatformTrend'),
    path('rating_views/', views.rating_views, name='rating_views'),

]