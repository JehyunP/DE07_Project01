from django.http import HttpResponse, HttpResponseRedirect
from .models import *
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.db.models import F
from django.views import generic
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count
import json

# Create your views here.
def index(request):
    program_lists = Program.objects.all()[:5]
    context = {'Program' : program_lists}

    return render(request, 'backends/index.html', context)


def detail(request, program_id):
    program = get_object_or_404(Program, pk=program_id)
    return render(request, 'backends/detail.html', {'program': program})

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