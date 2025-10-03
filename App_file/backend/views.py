from .models import *
from django.shortcuts import render, get_object_or_404
import pandas as pd
from django.db.models import Sum, Count, FloatField
from django.db.models.functions import Cast
from django.db.models.functions import RowNumber
from django.db.models import Window
from django.shortcuts import render
from .models import Performance
from django.db.models import F
from . import visualize
import ast




# Create your views here.
def index(request):
    program_lists = Program.objects.all()[:5]
    context = {'Program' : program_lists}

    return render(request, 'backends/index.html', context)


def detail(request, program_id):
    program = get_object_or_404(Program, pk=program_id)

    performances = program.performances.all().order_by("-half_year")  
    streamings = program.streamings.all()  
    directors = program.person_roles.filter(role__iexact="director")
    actors = program.person_roles.filter(role__iexact="starring")
    producers = program.person_roles.filter(role__iexact="producer")

    context = {
        "program": program,
        "performances": performances,
        "streamings": streamings,
        "directors": directors,
        "actors": actors,
        "producers": producers,
    }
    return render(request, "backends/detail.html", context)


def genreTrend(request):
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


def genreDetail(request):
    genre = request.GET.get("genre")
    half_year = request.GET.get("half_year")
    mode = request.GET.get("mode")

    qs = (
        Performance.objects
        .filter(half_year=half_year, program__genre__name=genre)
        .select_related("program")
        .order_by("-views" if mode == "views" else "-hours")[:5]
    )

    df = pd.DataFrame([
        {
            "id": p.program.id,
            "title": p.program.title,
            "views": p.views,
            "hours": p.hours
        }
        for p in qs
    ])

    chart_html = visualize.detail_bar_plot(df, genre, half_year, mode)

    return render(request, "backends/genre_detail.html", {"chart": chart_html})


def index(request):
    return render(request, 'backends/index.html')