# 파이썬 기본 유틸리티
from io import BytesIO
import base64
import random
import ast

from django.views import generic
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count
import json

# Django 기본 기능
from django.shortcuts import render, get_object_or_404

# Django ORM 기능
from django.db.models import Sum, Count, F, FloatField, Window, Avg
from django.db.models.functions import Cast, RowNumber, Floor

# 데이터 분석 / 시각화 라이브러리
import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from wordcloud import WordCloud

# 프로젝트 내부 모듈
from .models import *
from . import visualize
from .models import Performance

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
    year, half = half_year.split("-")
    half_kor = "상반기" if half == "1" else "하반기"
    half_year_display = f"{year}년 {half_kor}"

    context = {
        "half_year": half_year,
        "half_year_display": half_year_display,
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

    year, half = half_year.split("-")
    half_kor = "상반기" if half == "1" else "하반기"
    half_year_display = f"{year}년 {half_kor}"

    return render(request, "backends/subgenre_programs.html", {
        "subgenre": subgenre,
        "programs": programs_with_rank,
        "half_year": half_year,
        "half_year_display": half_year_display,
    })

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
    
    
# 스트리밍 플랫폼 뷰

# OTT 대표 색상
OTT_COLORS = {
    'Netflix': '#E50914',
    'Disney+': '#01147C',
    'Hulu': '#1CE783',
    'Amazon Prime': '#1399FF',
    'Apple TV+': '#000000',
    'HBO Max': '#9E86FF',
    'YouTube': '#FF0000',
    'Peacock': '#F5003A',
    'Paramount+': '#E50914',
    'Discovery+': '#FF6600'
}

# 워드클라우드 색상 함수
def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    if word in OTT_COLORS:
        return OTT_COLORS[word]
    r = random.randint(50, 200)
    g = random.randint(50, 200)
    b = random.randint(50, 200)
    return f"rgb({r},{g},{b})"

# 상/하반기 라벨 변환
def half_year_label(half_year):
    year, half = half_year.split("-")
    if half == "1":
        return f"{year}년 상반기"
    elif half == "2":
        return f"{year}년 하반기"
    return half_year

# WordCloud
def generate_wordcloud(freq_dict):
    wc = WordCloud(
        width=800,
        height=500,
        background_color='white',
        color_func=color_func,
        relative_scaling=0.75
    ).generate_from_frequencies(freq_dict)
    
    buffer = BytesIO()
    wc.to_image().save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode()
    
    fig = go.Figure(go.Image(source='data:image/png;base64,' + encoded))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        autosize=True,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return pio.to_html(fig, full_html=False, config={'responsive': True})

# Plotly Bar chart
def generate_bar_chart(df, xlabel, ylabel):
    fig = px.bar(
        df,
        x='OTT',
        y='Ratio',
        color='OTT',
        color_discrete_map=OTT_COLORS,
        hover_data={
            'Ratio': ':.2f',
            'Count': True,
            'OTT': False
        }
    )
    fig.update_layout(
        xaxis_title=xlabel,
        yaxis_title=ylabel,
        title_x=0.5,
        template='plotly_white',
        autosize=True,
        margin=dict(l=40, r=40, t=30, b=50),
        legend=dict(
            title_text="",
            orientation='h',
            x=0.5,
            y=-0.3,
            xanchor="center",
            yanchor="top"
        )
    )
    return pio.to_html(fig, full_html=False, config={'responsive': True})

# OTT 플랫폼 분석 대시보드 뷰
def ottplatformRank(request):
    performances = Performance.objects.all()
    data_list = []
    
    for performance in performances:
        program = performance.program
        for streaming in program.streamings.all():
            data_list.append({
                'half_year': performance.half_year,
                'ott': streaming.ott,
                'program_id': program.id,
                'title': program.title,
                'poster': program.poster,
                'views': performance.views,
            })
            
    df = pd.DataFrame(data_list)
    
    if df.empty:
        return render(request, 'backends/ottplatform.html', {
            'images_by_half': {},
            'title': 'OTT 플랫폼 시장 분석 (데이터 없음)',
            'first_half': None
        })
    
    results = {}
    
    for half in sorted(df["half_year"].unique()):
        df_half = df[df["half_year"] == half]
        label = half_year_label(half)
        
        # OTT별 보유 작품 수 비율
        ott_program_count = df_half.groupby("ott")["program_id"].nunique()
        ott_program_ratio = (ott_program_count / 300) * 100
        df_cnt_rat = pd.DataFrame({
            "OTT": ott_program_count.index,
            "Count": ott_program_count.values,
            "Ratio": ott_program_ratio.values
        })
        df_top10 = df_cnt_rat.sort_values(by="Ratio", ascending=False).head(10)
        
        # 시각화
        wc_html = generate_wordcloud(ott_program_count.to_dict())
        bar_html = generate_bar_chart(
            df_top10,
            "OTT 플랫폼", "점유율(%)"
        )
        
        # OTT별 인기작 Top3
        ott_top3 = {}
        for ott in df_half["ott"].unique():
            ranking = (
                df_half[df_half["ott"] == ott]
                .groupby(["program_id", "title", "poster"])["views"]
                .sum()
                .reset_index()
                .sort_values(by="views", ascending=False)
            )
            ott_top3[ott] = ranking.head(3).to_dict("records")
            
        results[half] = {
            "label": label,
            "charts": [
                {
                    "title": f"{label} OTT별 인기 작품 수",
                    "desc": "OTT별 인기 작품 수 워드클라우드",
                    "img": wc_html
                },{
                    "title": f"{label} OTT별 인기 작품 점유율 (Top 10)",
                    "desc": "OTT별 인기 작품 점유율 막대 차트",
                    "img": bar_html
                },
            ],
            "ott_top3": ott_top3
        }

    return render(request, "backends/ottplatform.html", {
        "results": results,
        "title": "OTT 플랫폼 시장 분석",
        "first_half": next(iter(results.keys()), None),
    })
    
    
def rating_views(request):
    data = Performance.objects.annotate(IMDb_rating=Floor('imdb')).values('IMDb_rating').annotate(avg_views=Avg('views')).order_by('IMDb_rating')
    max_avg_views = data.order_by('-avg_views')[0].get('avg_views')
    top_rating = int(max(data, key=lambda x: x['avg_views'])['IMDb_rating'])

    programs_by_rating = {}
    for rating in range(0, 11):
        programs = (
            Performance.objects
            .annotate(int_rating=Floor('imdb'))
            .filter(int_rating=rating)
            .select_related('program')
            .order_by('-views')
            .values('program__title', 'views')
        )[:16]

        programs_by_rating[rating] = list(programs)
    
    top_programs = programs_by_rating.get(top_rating, [])

    fig = px.bar(data, x='IMDb_rating', y='avg_views', title='평점 별 평균 조회수')
    fig.update_layout(title_x=0.5, autosize=True, height=750, width=800, margin=dict(t=50, b=50, l=50, r=50))
    fig.update_yaxes(range=[max_avg_views*0.6, max_avg_views*1.1], title='평균 시청수')
    fig.update_xaxes(title='IMDb 평점')

    chart_html = fig.to_html(full_html=False)

    return render(request, 'backends/rating_views.html', {'chart': chart_html, 'programs_by_rating':programs_by_rating, 'top_programs':top_programs, 'top_rating':top_rating})
