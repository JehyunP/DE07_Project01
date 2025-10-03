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
<<<<<<< HEAD
from django.views import generic
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count
import json
=======
from . import visualize
import ast



>>>>>>> 66e4cc1601c7ba2d44297f8126b0278416b6030c

# Create your views here.
def index(request):
    program_lists = Program.objects.all()[:5]
    context = {'Program' : program_lists}

    return render(request, 'backends/index.html', context)


def detail(request, program_id):
    program = get_object_or_404(Program, pk=program_id)

<<<<<<< HEAD
'''
def subgenreportion(request, genre_name):
    genre = get_object_or_404(Genre, name=genre_name)

    # 서브장르와 프로그램 개수 집계 후 내림차순 정렬
    subgenres = (
        SubGenre.objects.filter(genre=genre)
        .annotate(program_count=Count("program"))
        .order_by('-program_count')  # ← 내림차순 정렬
    )

    labels = [sg.name for sg in subgenres]
    data = [sg.program_count for sg in subgenres]

    context = {
        "genre_name": genre.name,
        "labels": json.dumps(labels, ensure_ascii=False),
        "data": json.dumps(data),
    }
    return render(request, "backends/subgenreportion.html", context)

def genreportion(request, half_year):
    # 1. 특정 half_year 기준으로 Performance에서 Program-Genre 카운트
    data = (
        Performance.objects.filter(half_year=half_year)
        .values("program__genre__name")
        .annotate(count=Count("program__id"))
        .order_by("-count")
    )

    # 2. labels / data 리스트 생성
    labels = [item["program__genre__name"] for item in data]
    counts = [item["count"] for item in data]

    # 3. context에 JSON 직렬화하여 넘기기
    context = {
        "half_year": half_year,
        "labels": json.dumps(labels, ensure_ascii=False),
        "data": json.dumps(counts),
    }
    return render(request, "backends/genreportion.html", context)
'''

def genre_distribution(request, half_year):
    data = (
        Performance.objects.filter(half_year=half_year)
        .values("program__genre__name", "program__genre__id")
        .annotate(count=Count("program"))
        .order_by("-count")
    )
    labels = [item["program__genre__name"] for item in data]
    ids = [item["program__genre__id"] for item in data]
    counts = [item["count"] for item in data]

    context = {
        "half_year": half_year,
        "labels": json.dumps(labels, ensure_ascii=False),
        "ids": json.dumps(ids),
        "data": json.dumps(counts),
    }
    return render(request, "backends/genrensub.html", context)

from django.http import JsonResponse

def subgenre_distribution_api(request, genre_id, half_year):
    data = (
        Performance.objects.filter(half_year=half_year, program__genre__id=genre_id)
        .values("program__sub_genre__id", "program__sub_genre__name")
        .annotate(count=Count("program"))
        .order_by("-count")
    )

    labels = [item["program__sub_genre__name"] or "기타" for item in data]
    counts = [item["count"] for item in data]
    ids = [item["program__sub_genre__id"] for item in data]

    return JsonResponse({"labels": labels, "data": counts, "ids": ids})

def subgenre_programs(request, subgenre_id, half_year):
    subgenre = get_object_or_404(SubGenre, id=subgenre_id)

    programs = (
        Program.objects.filter(sub_genre=subgenre, performances__half_year=half_year)
        .order_by("-performances__views")
        .select_related("sub_genre")
        .prefetch_related("performances")
    )

    # 순위 매기기
    programs_with_rank = []
    for idx, program in enumerate(programs, start=1):
        perf = program.performances.filter(half_year=half_year).first()
        if perf:
            programs_with_rank.append({
                "rank": idx,
                "program": program,
                "views": f"{perf.views:,}",
            })

    return render(request, "backends/subgenre_programs.html", {
        "subgenre": subgenre,
        "programs": programs_with_rank,
        "half_year": half_year,
    })
=======
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
>>>>>>> 66e4cc1601c7ba2d44297f8126b0278416b6030c
