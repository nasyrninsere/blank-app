"""
SAYOUNG 비즈니스 대시보드 - 단일 파일 고도화 버전
(사용자 요청에 따라 pages, utils 폴더 없이 단일 파일로 병합)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

# =====================================================================
# 1. 페이지 및 공통 설정
# =====================================================================
st.set_page_config(
    page_title="SAYOUNG 비즈니스 대시보드",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 브랜드 컬러 팔레트
BRAND_COLORS = ["#0077B6", "#00B4D8", "#90E0EF", "#CAF0F8", "#023E8A"]
PRIMARY = "#0077B6"

st.markdown("""
<style>
/* 테마 컬러 연동 (config.toml 대신 하드코딩) */
:root {
  --primary-color: #0077B6;
  --background-color: #F0F4F8;
}
/* KPI 카드 */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e0e8f0;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,119,182,0.08);
}
[data-testid="stMetricLabel"] { font-size: 0.85rem; color: #5a7fa0; }
[data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; color: #0077B6; }
/* 사이드바 헤더 */
section[data-testid="stSidebar"] h2 { color: #0077B6; }
/* 페이지 타이틀 */
h1 { color: #0077B6 !important; letter-spacing: -0.5px; }
/* 구분선 */
hr { border-color: #e0e8f0; }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# 2. 데이터 로더 모듈 (utils/data_loader.py 내용 병합)
# =====================================================================
@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    np.random.seed(42)
    dates = pd.date_range(start="2026-01-01", end="2026-03-18")
    branches = ["광안리 본점", "해운대점", "남포동점"]
    menus = ["시그니처 샌드 커피", "아메리카노", "레몬 머랭 파이", "피칸 파이", "라떼"]
    weathers = ["맑음", "흐림", "비", "눈"]
    hours = list(range(9, 22))

    weights = [1, 2, 3, 5, 4, 2, 3, 6, 5, 3, 2, 2, 1]
    hour_probs = [w / sum(weights) for w in weights]

    records = []
    for branch in branches:
        for d in dates:
            branch_factor = {"광안리 본점": 1.0, "해운대점": 0.85, "남포동점": 0.70}[branch]
            weather = np.random.choice(weathers, p=[0.55, 0.25, 0.15, 0.05])
            weather_factor = {"맑음": 1.1, "흐림": 1.0, "비": 0.8, "눈": 0.75}[weather]
            dow = d.weekday()
            dow_factor = 1.0 if dow == 5 else (0.9 if dow == 6 else 0.75)

            base_visitors = int(np.random.randint(50, 300) * branch_factor * weather_factor * dow_factor)
            base_sales = int(np.random.randint(500_000, 3_000_000) * branch_factor * weather_factor * dow_factor)
            peak_hour = np.random.choice(hours, p=hour_probs)

            records.append({
                "날짜": d, "지점": branch, "방문자수": base_visitors, "매출액": base_sales,
                "객단가": base_sales // max(base_visitors, 1), "인기메뉴": np.random.choice(menus),
                "날씨": weather, "피크시간대": f"{peak_hour:02d}시",
                "요일": ["월", "화", "수", "목", "금", "토", "일"][dow],
                "신규고객수": int(base_visitors * np.random.uniform(0.1, 0.3)),
            })

    df = pd.DataFrame(records)
    df["날짜"] = pd.to_datetime(df["날짜"])
    return df

def compute_kpi(df: pd.DataFrame, prev_df: pd.DataFrame) -> dict:
    def pct(curr, prev):
        return f"{((curr - prev) / prev * 100):+.1f}%" if prev else None
    
    cv, cs = df["방문자수"].sum(), df["매출액"].sum()
    cas, cup = df.groupby("날짜")["매출액"].sum().mean(), df["객단가"].mean()
    cn = df["신규고객수"].sum()
    
    pv = prev_df["방문자수"].sum() if not prev_df.empty else 0
    ps = prev_df["매출액"].sum() if not prev_df.empty else 0
    pas = prev_df.groupby("날짜")["매출액"].sum().mean() if not prev_df.empty else 0
    pup = prev_df["객단가"].mean() if not prev_df.empty else 0
    pn = prev_df["신규고객수"].sum() if not prev_df.empty else 0

    return {
        "총 방문자수": (f"{cv:,}명", pct(cv, pv)),
        "총 매출액": (f"₩{cs:,}", pct(cs, ps)),
        "일평균 매출": (f"₩{int(cas):,}", pct(cas, pas)),
        "평균 객단가": (f"₩{int(cup):,}", pct(cup, pup)),
        "신규 고객수": (f"{cn:,}명", pct(cn, pn)),
    }

# =====================================================================
# 3. 차트 컴포넌트 모듈 (utils/charts.py 내용 병합)
# =====================================================================
def chart_line_ma(df, x, y, ma_windows=(7, 30), title=""):
    day_df = df.groupby(x)[y].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=day_df[x], y=day_df[y], mode="lines+markers", name="일별", line=dict(color=PRIMARY, width=2)))
    colors_ma = ["#FF6B35", "#06A77D"]
    for i, w in enumerate(ma_windows):
        if len(day_df) >= w:
            ma = day_df[y].rolling(w).mean()
            fig.add_trace(go.Scatter(x=day_df[x], y=ma, mode="lines", name=f"{w}일 평균", line=dict(color=colors_ma[i], width=2, dash="dot")))
    fig.update_layout(title=title, hovermode="x unified", legend=dict(orientation="h", y=1.02), plot_bgcolor="white", paper_bgcolor="white")
    return fig

def chart_gauge(value, reference, title=""):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=value,
        delta={"reference": reference, "relative": True, "valueformat": ".1%"},
        number={"prefix": "₩", "valueformat": ",.0f"}, title={"text": title},
        gauge={
            "axis": {"range": [0, max(reference * 1.5, 1)]}, "bar": {"color": PRIMARY},
            "steps": [{"range": [0, reference * 0.7], "color": "#FFE0E0"}, {"range": [reference * 0.7, reference], "color": "#FFF3CD"}, {"range": [reference, reference * 1.5], "color": "#D4EDDA"}],
            "threshold": {"line": {"color": "red", "width": 3}, "thickness": 0.75, "value": reference},
        }
    ))
    fig.update_layout(paper_bgcolor="white", height=280)
    return fig


# =====================================================================
# 4. 각 페이지 렌더링 함수
# =====================================================================

def render_home(df, selected_branch, start_d, end_d, filtered_df):
    period_days = (end_d - start_d).days
    prev_end = start_d - pd.Timedelta(days=1)
    prev_start = prev_end - pd.Timedelta(days=period_days)
    prev_mask = (df["날짜"].dt.date >= prev_start) & (df["날짜"].dt.date <= prev_end)
    if selected_branch != "전체": prev_mask &= df["지점"] == selected_branch
    prev_df = df[prev_mask]

    st.title("🌊 SAYOUNG 비즈니스 대시보드")
    st.markdown(f"**{selected_branch if selected_branch!='전체' else '전체 지점'}** | {start_d} ~ {end_d} *({period_days + 1}일)*")
    st.divider()

    kpi = compute_kpi(filtered_df, prev_df)
    cols = st.columns(5)
    for i, (label, (val, delta)) in enumerate(kpi.items()):
        cols[i].metric(label, val, delta)
    st.divider()

    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("📈 일별 매출 추이")
        day_sales = filtered_df.groupby(["날짜", "지점"])["매출액"].sum().reset_index()
        fig = px.line(day_sales, x="날짜", y="매출액", color="지점", color_discrete_sequence=BRAND_COLORS, markers=True, line_shape="spline")
        fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1), plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("🏪 지점별 매출 비중")
        branch_sales = filtered_df.groupby("지점")["매출액"].sum().reset_index()
        fig2 = px.pie(branch_sales, values="매출액", names="지점", hole=0.45, color_discrete_sequence=BRAND_COLORS)
        fig2.update_traces(textposition="outside", textinfo="percent+label")
        fig2.update_layout(showlegend=False, paper_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)

def render_trend(df, selected_branch, start_d, end_d, filtered_df):
    st.title("📈 트렌드 분석")
    st.divider()
    
    agg_unit = st.radio("집계 단위", ["일별", "주별", "월별"], horizontal=True)
    freq = {"일별": "D", "주별": "W-MON", "월별": "ME"}[agg_unit]
    agg_df = filtered_df.set_index("날짜").groupby("지점").resample(freq)[["매출액","방문자수"]].sum().reset_index()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 매출액", f"₩{filtered_df['매출액'].sum():,}")
    c2.metric("총 방문자", f"{filtered_df['방문자수'].sum():,}명")
    c3.metric("최고 일매출", f"₩{filtered_df.groupby('날짜')['매출액'].sum().max():,}")
    c4.metric("최저 일매출", f"₩{filtered_df.groupby('날짜')['매출액'].sum().min():,}")
    st.divider()

    st.subheader(f"지점별 매출 추이 ({agg_unit})")
    if selected_branch != "전체":
        fig = chart_line_ma(agg_df[agg_df["지점"] == selected_branch], "날짜", "매출액")
    else:
        fig = px.bar(agg_df, x="날짜", y="매출액", color="지점", barmode="stack", color_discrete_sequence=BRAND_COLORS)
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("주간 캔들스틱")
    day_df = filtered_df.groupby("날짜")["매출액"].sum().reset_index()
    day_df["주차"] = day_df["날짜"].dt.to_period("W").dt.start_time
    weekly = day_df.groupby("주차")["매출액"].agg(["min", "max", "first", "last"]).reset_index()
    weekly.columns = ["날짜", "low", "high", "open", "close"]
    fig3 = go.Figure(go.Candlestick(x=weekly["날짜"], open=weekly["open"], high=weekly["high"], low=weekly["low"], close=weekly["close"]))
    fig3.update_layout(xaxis_rangeslider_visible=False, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig3, use_container_width=True)

def render_menu(df, selected_branch, start_d, end_d, filtered_df):
    st.title("🥧 메뉴 분석")
    st.divider()
    
    menu_stats = filtered_df.groupby("인기메뉴").agg(판매일수=("인기메뉴", "count"), 총매출=("매출액", "sum")).reset_index()
    if menu_stats.empty:
        st.warning("조건에 맞는 데이터가 없습니다.")
        return

    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("메뉴별 판매 랭킹")
        fig_bar = px.bar(menu_stats.sort_values("판매일수"), x="판매일수", y="인기메뉴", orientation="h", color="판매일수", color_continuous_scale="Blues")
        fig_bar.update_layout(coloraxis_showscale=False, plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_bar, use_container_width=True)
    with c2:
        st.subheader("메뉴별 매출 비중")
        fig_pie = px.pie(menu_stats, values="총매출", names="인기메뉴", hole=0.4, color_discrete_sequence=BRAND_COLORS)
        fig_pie.update_traces(textposition="outside", textinfo="percent+label")
        fig_pie.update_layout(showlegend=False, paper_bgcolor="white")
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("지점 → 메뉴 계층 선버스트")
    grouped = filtered_df.groupby(["지점", "인기메뉴"]).size().reset_index(name="판매일수")
    fig_sun = px.sunburst(grouped, path=["지점", "인기메뉴"], values="판매일수", color_discrete_sequence=BRAND_COLORS)
    fig_sun.update_layout(paper_bgcolor="white")
    st.plotly_chart(fig_sun, use_container_width=True)

def render_customer(df, selected_branch, start_d, end_d, filtered_df):
    st.title("👥 고객 분석")
    st.divider()

    st.subheader("방문자수 ↔ 매출액 상관관계 (날씨별)")
    fig = px.scatter(filtered_df, x="방문자수", y="매출액", color="날씨", size="객단가", facet_col="지점", color_discrete_map={"맑음": "#0077B6", "흐림": "#888", "비": "#00B4D8", "눈": "#CAF0F8"}, trendline="ols")
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("고객 유입 퍼널")
    total = filtered_df["방문자수"].sum()
    new_c = filtered_df["신규고객수"].sum()
    fig_f = go.Figure(go.Funnel(y=["전체 방문자", "구매 고객", "재방문 고객", "고가치 고객"], x=[total, int(total*0.85), total-new_c, int(total*0.3)], textinfo="value+percent initial", marker=dict(color=BRAND_COLORS[:4])))
    fig_f.update_layout(paper_bgcolor="white")
    st.plotly_chart(fig_f, use_container_width=True)

def render_data(df, selected_branch, start_d, end_d, filtered_df):
    st.title("📋 데이터 관리")
    st.divider()

    st.subheader("🎯 월별 매출 목표 설정")
    filtered_df = filtered_df.copy()
    filtered_df["월"] = filtered_df["날짜"].dt.to_period("M").astype(str)
    monthly_actual = filtered_df.groupby("월")["매출액"].sum().reset_index()

    if "goal_df" not in st.session_state:
        st.session_state.goal_df = pd.DataFrame({"월": monthly_actual["월"].tolist(), "목표매출": [int(v * 1.1) for v in monthly_actual["매출액"].tolist()]})
    
    edited = st.data_editor(st.session_state.goal_df, use_container_width=True, hide_index=True, column_config={"목표매출": st.column_config.NumberColumn(format="₩%d")})
    if st.button("목표 적용"): st.session_state.goal_df = edited

    merged = monthly_actual.merge(st.session_state.goal_df, on="월", how="left").fillna({"목표매출": 0})
    gauge_cols = st.columns(min(len(merged), 3) if len(merged)>0 else 1)
    for i, (_, row) in enumerate(merged.iterrows()):
        with gauge_cols[i % len(gauge_cols)]:
            st.plotly_chart(chart_gauge(row["매출액"], row["목표매출"], f"{row['월']}"), use_container_width=True)

    st.subheader("전체 데이터 조회 및 다운로드")
    st.dataframe(filtered_df, use_container_width=True)
    csv = filtered_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 CSV 다운로드", data=csv, file_name="sayoung_data.csv", mime="text/csv")


# =====================================================================
# 5. 메인 실행 & 라우팅 분기
# =====================================================================
df = load_data()

with st.sidebar:
    st.markdown("## ⚙️ 대시보드 설정")
    page = st.radio("메뉴 이동", ["홈", "📈 트렌드 분석", "🥧 메뉴 분석", "👥 고객 분석", "📋 데이터 관리"])
    st.divider()

    branches = ["전체"] + sorted(df["지점"].unique().tolist())
    selected_branch = st.selectbox("지점", branches)
    
    min_date, max_date = df["날짜"].dt.date.min(), df["날짜"].dt.date.max()
    date_range = st.date_input("조회 기간", [min_date, max_date])

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_d, end_d = date_range
else:
    start_d, end_d = min_date, max_date

mask = (df["날짜"].dt.date >= start_d) & (df["날짜"].dt.date <= end_d)
if selected_branch != "전체": mask &= df["지점"] == selected_branch
filtered_df = df[mask]

# 선택된 페이지 렌더링
if page == "홈": render_home(df, selected_branch, start_d, end_d, filtered_df)
elif page == "📈 트렌드 분석": render_trend(df, selected_branch, start_d, end_d, filtered_df)
elif page == "🥧 메뉴 분석": render_menu(df, selected_branch, start_d, end_d, filtered_df)
elif page == "👥 고객 분석": render_customer(df, selected_branch, start_d, end_d, filtered_df)
elif page == "📋 데이터 관리": render_data(df, selected_branch, start_d, end_d, filtered_df)
