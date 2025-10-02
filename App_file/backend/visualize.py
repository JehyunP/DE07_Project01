import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px

def rank_half_year_plot(df):
    genres = df['genre'].unique()
    df_top10_view = df[df['view_rank'] <= 10]
    df_top10_hour = df[df['hour_rank'] <= 10]

    
    order = sorted(df["half_year"].unique())

    fig = go.Figure()
    colors = px.colors.qualitative.Set2
    color_map = {g: colors[i % len(colors)] for i, g in enumerate(genres)}

    view_idxs, hour_idxs = [], []

    # ---------------------------
    # 조회수 랭킹 (view_rank)
    # ---------------------------
    for g in df_top10_view['genre'].unique():
        data = df_top10_view[df_top10_view['genre'] == g]

        # glow line
        view_idxs.append(len(fig.data))
        fig.add_trace(go.Scatter(
            x=data['half_year'], y=data['view_rank'],
            mode='lines',
            line=dict(width=10, color=color_map[g]),
            opacity=0.15,
            hoverinfo='skip',
            showlegend=False,
            visible=True
        ))

        # main line
        view_idxs.append(len(fig.data))
        fig.add_trace(go.Scatter(
            x=data["half_year"], y=data["view_rank"],
            mode="lines+markers",
            name=g,
            line=dict(width=3, color=color_map[g]),
            marker=dict(size=8, symbol="circle"),
            visible=True
        ))

    # ---------------------------
    # 시청시간 랭킹 (hour_rank)
    # ---------------------------
    for g in df_top10_hour["genre"].unique():
        data = df_top10_hour[df_top10_hour["genre"] == g]

        # glow
        hour_idxs.append(len(fig.data))
        fig.add_trace(go.Scatter(
            x=data["half_year"], y=data["hour_rank"],
            mode="lines",
            line=dict(width=10, color=color_map[g]),
            opacity=0.15,
            hoverinfo="skip",
            showlegend=False,
            visible=False
        ))

        # main
        hour_idxs.append(len(fig.data))
        fig.add_trace(go.Scatter(
            x=data["half_year"], y=data["hour_rank"],
            mode="lines+markers",
            name=g,
            line=dict(width=3, color=color_map[g]),
            marker=dict(size=8, symbol="circle"),
            visible=False
        ))

    # ---------------------------
    # 마스크 생성
    # ---------------------------
    def mask(indices_true):
        m = [False] * len(fig.data)
        for i in indices_true:
            m[i] = True
        return m

    view_mask = mask(view_idxs)
    hour_mask = mask(hour_idxs)

    # ---------------------------
    # Layout & Dropdown
    # ---------------------------
    fig.update_layout(
        title=dict(
            text="반기별 장르 트렌드 변화",
            x=0.435,              
            y=0.95,             
            xanchor="center",
            yanchor="top",
            font=dict(
                size=24, 
                family="Arial Black", 
                color="darkblue"
            )
        ),
        xaxis=dict(
            title=dict(text='반기 (Half-Year)', font=dict(size=16, family="Verdana", color="black")),
            tickfont=dict(size=12, family="Courier New", color="gray"),
            type="category",
            categoryorder="array", categoryarray=order
        ),
        yaxis=dict(
            title=dict(text="조회수 랭킹", font=dict(size=16, family="Verdana", color="black")),
            tickfont=dict(size=12, family="Courier New", color="gray"),
            autorange="reversed", dtick=1
        ),
        legend=dict(
            title="장르",
            orientation="v",
            x=1.02, y=1,
            xanchor="left", yanchor="top",
            bgcolor="rgba(255,255,255,0.6)",
            bordercolor="black", borderwidth=1
        ),
        margin=dict(l=40, r=200, t=80, b=80),
        plot_bgcolor="white",
        updatemenus=[dict(
            type="dropdown",
            showactive=True,
            x=0.1, y=1.15, xanchor="right", yanchor="top",
            buttons=[
                dict(
                    label="조회수 랭킹",
                    method="update",
                    args=[{"visible": view_mask},
                        {"yaxis": {"title": {"text": "조회수 랭킹"},
                                    "autorange": "reversed", "dtick": 1}}]
                ),
                dict(
                    label="시청시간 랭킹",
                    method="update",
                    args=[{"visible": hour_mask},
                        {"yaxis": {"title": {"text": "시청시간 랭킹"},
                                    "autorange": "reversed", "dtick": 1}}]
                ),
            ]
        )]
    )

    return pio.to_html(fig, full_html=False)
