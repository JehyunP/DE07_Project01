# 파이썬 기본 유틸리티
from io import BytesIO
import base64
import random
import ast

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
    
    
    
    
    
# ==================================================
# 스트리밍 플랫폼 관련 분석 및 시각화 뷰
# ==================================================

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


# Plotly Bar chart
def generate_bar_chart(df, title, xlabel, ylabel):
    fig = px.bar(
        df,
        x='OTT',
        y='Ratio',
        color='OTT',
        color_discrete_map=OTT_COLORS,
        title=title,
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
        margin=dict(l=40, r=40, t=60, b=80),
        legend=dict(
            title_text="",
            orientation='h',
            x=0.5,
            y=-0.3,
            xanchor="center",
            yanchor="top"
        )
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={'responsive': True})

# WordCloud
def generate_wordcloud(freq_dict):
    wc = WordCloud(
        width=800,
        height=500,
        background_color='white',
        max_words=30,
        color_func=color_func,
        relative_scaling=0.5
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

# 연도+상/하반기 라벨 변환
def half_year_label(half_year):
    year, half = half_year.split("-")
    if half == "1":
        return f"{year}년 상반기"
    elif half == "2":
        return f"{year}년 하반기"
    return half_year

# OTT 플랫폼 분석 대시보드 뷰
def ottplatformTrend(request):
    performances = Performance.objects.all()
    data_list = []

    for performance in performances:
        program = performance.program   # 여기서 매번 쿼리 발생
        for streaming in program.streamings.all():  # 여기서도 매번 쿼리 발생
            data_list.append({
                'half_year': performance.half_year,
                'ott': streaming.ott,
                'program_id': program.id,
                'views': performance.views,
                'country': program.country
            })

    df = pd.DataFrame(data_list)

    if df.empty:
        return render(request, 'backends/ottplatform.html', {
            'images_by_half': {},
            'title': 'OTT 시장 분석 대시보드 (데이터 없음)',
            'first_half': None
        })

    images_by_half = {}

    for half in sorted(df['half_year'].unique()):
        df_half = df[df['half_year'] == half]
        label = half_year_label(half)

        # OTT 별 보유 작품 수, 비율
        ott_program_count = df_half.groupby('ott')['program_id'].nunique()
        ott_program_ratio = ((ott_program_count / 300) * 100)
        df_cnt_rat = pd.DataFrame({
            'OTT': ott_program_count.index,
            'Count': ott_program_count.values,
            'Ratio': ott_program_ratio.values
        })
        df_top10 = df_cnt_rat.sort_values(by='Ratio', ascending=False).head(10)

        # 인기 작품 지수
        grouped = df_half.groupby('ott').agg(
            total_views=('views', 'sum'),
            program_count=('program_id', 'nunique')
        ).reset_index()
        grouped['view_index'] = (
            (grouped['total_views'] / grouped['program_count']) * (grouped['program_count'] / 300)
        )

        # 1. 바 차트
        bar_html = generate_bar_chart(
            df_top10,
            f'{label} OTT별 작품 점유율 Top 10',
            'OTT 플랫폼', '점유율(%)'
        )

        # 2. 워드클라우드
        wc_html = generate_wordcloud(ott_program_count.to_dict())

        # 3. 공급 대비 히트율 분석
        supply = df_half.groupby('ott')['program_id'].nunique().reset_index(name='supply')

        # 히트작 기준: views 상위 20%
        # threshold = df_half['views'].quantile(0.8)
        # hits = (
        #     df_half[df_half['views'] >= threshold]
        #     .groupby('ott')['program_id']
        #     .nunique()
        #     .reset_index(name='hits')
        # )

        # result = supply.merge(hits, on='ott', how='left').fillna(0)
        # result['hit_ratio'] = (result['hits'] / result['supply']) * 100

        # fig = go.Figure()
        # fig.add_trace(go.Bar(x=result['ott'], y=result['supply'], name="공급량"))
        # fig.add_trace(go.Bar(x=result['ott'], y=result['hits'], name="히트작"))
        # fig.add_trace(go.Scatter(
        #     x=result['ott'], y=result['hit_ratio'],
        #     mode='lines+markers', name="히트율 (%)", yaxis="y2"
        # ))

        # fig.update_layout(
        #     title=f"{label} - OTT별 공급 대비 히트율",
        #     yaxis=dict(title="작품 수"),
        #     yaxis2=dict(title="히트율 (%)", overlaying="y", side="right"),
        #     barmode='group',
        #     title_x=0.5
        # )

        # hit_chart_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={'responsive': True})

        images_by_half[half] = {
            "label": label,
            "charts": [
                {
                    'title': f'{label} - OTT별 보유 작품 비율 (Top 10)',
                    'desc': 'Top 10 OTT 비율 막대 차트',
                    'img': bar_html
                },
                {
                    'title': f'{label} - OTT 워드클라우드',
                    'desc': '전체 OTT 워드클라우드 (보유작 기준)',
                    'img': wc_html
                },
                # {
                #     'title': f'{label} - OTT 공급 대비 히트율',
                #     'desc': '공급량 대비 실제 인기 있는 작품 비율을 나타냅니다.',
                #     'img': hit_chart_html
                # }
            ]
        }

    return render(request, 'backends/ottplatform.html', {
        'images_by_half': images_by_half,
        'title': 'OTT 플랫폼 시장 분석',
        'first_half': next(iter(images_by_half.keys()), None)
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
    fig.update_layout(title_x=0.5, autosize=True, height=800, width=1100, margin=dict(t=50, b=50, l=50, r=50))
    fig.update_yaxes(range=[max_avg_views*0.6, max_avg_views*1.1], title='평균 시청수')
    fig.update_xaxes(title='IMDb 평점')

    chart_html = fig.to_html(full_html=False)

    return render(request, 'backends/rating_views.html', {'chart': chart_html, 'programs_by_rating':programs_by_rating, 'top_programs':top_programs, 'top_rating':top_rating})
