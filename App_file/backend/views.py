from .models import *
from django.shortcuts import render, get_object_or_404
import pandas as pd
import plotly.express as px
import plotly.io as pio
from django.db.models import Sum, Count, FloatField
from django.db.models.functions import Cast
from django.db.models.functions import RowNumber
from django.db.models import Window
from django.shortcuts import render
from .models import Performance
from django.db.models import F
from . import visualize


# Create your views here.
def index(request):
    program_lists = Program.objects.all()[:5]
    context = {'Program' : program_lists}

    return render(request, 'backends/index.html', context)


def detail(request, program_id):
    program = get_object_or_404(Program, pk=program_id)
    return render(request, 'backends/detail.html', {'program': program})


def genreTrand(request):
    qs = (
        Performance.objects.
        values('half_year', 'program__genre__name')
        .annotate(
            total_views = Sum('views'),
            total_hours = Sum('hours'),
            program_count = Count('program', distinct=True)
        )
    )

    df = pd.DataFrame(qs)
    
    df.rename(columns = {'program__genre__name' : 'genre'}, inplace=True)
    df['view_index'] = (df['total_views'] / df['program_count']) * (df['program_count'] / 300)
    df['view_rank'] = df.groupby('half_year')['view_index'].rank(
        method='dense', ascending=False
    )

    df['hour_index'] = (df['total_hours'] / df['program_count']) * (df['program_count'] / 300)
    df['hour_rank'] = df.groupby('half_year')['hour_index'].rank(
        method='dense', ascending=False
    )

    chart_html = visualize.rank_half_year_plot(df)


    return render(
        request, 'backends/genre_ranking_trend.html',
        {
            'chart_drop': chart_html
        }
    )




def index(request):
    program_lists = Program.objects.all()[:5]
    context = {'Program' : program_lists}
    top_program = Performance.objects.filter(rank=1, half_year='2025-1').select_related('program').first().program
    total_program_count = Program.objects.count()
    trend_program_genre_name = Performance.objects.values('program__genre__name').annotate(views_total=Sum('views'), genre_program_count=Count('program', distinct=True), avg_views=Cast(Sum('views'), FloatField()) / Count('program', distinct=True), weight=Cast(Count('program', distinct=True), FloatField()) / total_program_count, score=(Cast(Sum('views'), FloatField()) / Count('program', distinct=True)) * (Cast(Count('program', distinct=True), FloatField()) / total_program_count)).order_by('-score')[0].get('program__genre__name')
    trend_program = Program.objects.filter(genre__name=trend_program_genre_name).order_by('-performances__views')[:5]
    country_program = (Performance.objects.annotate(country=F('program__country'), row_number=Window(expression=RowNumber(), partition_by=[F('program__country')], order_by=F('views').desc())).filter(row_number__lte=1).select_related('program'))[:3]
    genre_program = (Performance.objects.annotate(country=F('program__genre'), row_number=Window(expression=RowNumber(), partition_by=[F('program__genre')], order_by=F('views').desc())).filter(row_number__lte=1).select_related('program'))[:3]
    return render(request, 'backends/index.html', {'context':context, 'top_program': top_program, 'trend_program_genre_name':trend_program_genre_name, 'trend_program':trend_program, 'country_program':country_program, 'genre_program':genre_program})