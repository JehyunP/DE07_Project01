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


def setGenreIndex():
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

    # ---- 프로그램 상세를 위한 별도 쿼리 ----
    qs_raw = Performance.objects.values(
        'id',
        'half_year',
        'views',
        'hours',
        'program__id',
        'program__title',
        'program__poster',
        'program__genre__name'
    )
    df_raw = pd.DataFrame(qs_raw)
    df_raw.rename(columns={
        'program__id': 'program_id',
        'program__title': 'title',
        'program__poster': 'poster',
        'program__genre__name': 'genre'
    }, inplace=True)
    df_all = df.merge(df_raw, on=['half_year', 'genre'], how='left')

    return df, df_all


def genreTrend(request):
    chart_html = visualize.rank_half_year_plot(setGenreIndex()[0])


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
    qs = (
        Performance.objects
        .filter(half_year = '2025-1')
        .select_related('program')
        .order_by('-views')[0]
    )

    poster = qs.program.poster
    df = setGenreIndex()[1]
    top_genre_row = (
        df[df['half_year'] == '2025-1']
        .sort_values(by='view_rank')
        .iloc[0]
    )
    genre_name = top_genre_row['genre']

    # 2. 해당 장르 & 2025-1의 프로그램 중 views 상위 5개
    genre_top5 = (
        df[(df['half_year'] == '2025-1') & (df['genre'] == genre_name)]
        .sort_values(by='views', ascending=False)
        .head(5)
    )
    genre_top5_list = genre_top5[['program_id', 'title', 'poster', 'views']].to_dict(orient='records')
    

    return render (
        request, 'backends/index.html', {
            'poster' : poster, 
            'top_program' : qs.program,
            'genre_top5' : genre_top5_list,
            'top_genre' : genre_name
        }   
    )