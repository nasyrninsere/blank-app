import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
from utils.data_loader import load_data, compute_kpi

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SAYOUNG 비즈니스 대시보드",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 커스텀 CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
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
/* 네비게이션 카드 */
.nav-card {
    background: linear-gradient(135deg, #0077B6 0%, #00B4D8 100%);
    border-radius: 12px;
    padding: 20px;
    color: white;
    text-align: center;
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 8px;
    box-shadow: 0 4px 12px rgba(0,119,182,0.25);
}
</style>
""", unsafe_allow_html=True)

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
df = load_data()

# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/ocean.png", width=64)
    st.markdown("## ⚙️ 대시보드 설정")
    st.divider()

    # 지점 선택
    all_branches = ["전체"] + sorted(df["지점"].unique().tolist())
    selected_branch = st.selectbox(
        "🏪 지점 선택",
        all_branches,
        key="home_branch",
    )

    # 날짜 범위
    min_date = df["날짜"].dt.date.min()
    max_date = df["날짜"].dt.date.max()
    date_range = st.date_input("📅 조회 기간", [min_date, max_date], key="home_date")

    # 빠른 기간 단축버튼
    st.markdown("**빠른 기간 선택**")
    col_a, col_b = st.columns(2)
    if col_a.button("이번 달", use_container_width=True):
        st.session_state["home_date"] = [
            pd.Timestamp("2026-03-01").date(), max_date
        ]
    if col_b.button("전체 기간", use_container_width=True):
        st.session_state["home_date"] = [min_date, max_date]

    st.divider()
    st.caption("🔄 데이터는 5분마다 자동 갱신됩니다.")

# ── 데이터 필터링 ─────────────────────────────────────────────────────────────
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_d, end_d = date_range
else:
    start_d, end_d = min_date, max_date

mask = (df["날짜"].dt.date >= start_d) & (df["날짜"].dt.date <= end_d)
if selected_branch != "전체":
    mask &= df["지점"] == selected_branch
filtered_df = df[mask]

# 이전 기간 (같은 일 수)
period_days = (end_d - start_d).days
prev_end = start_d - pd.Timedelta(days=1)
prev_start = prev_end - pd.Timedelta(days=period_days)
prev_mask = (df["날짜"].dt.date >= prev_start) & (df["날짜"].dt.date <= prev_end)
if selected_branch != "전체":
    prev_mask &= df["지점"] == selected_branch
prev_df = df[prev_mask]

# ── 메인 화면 ─────────────────────────────────────────────────────────────────
st.title("🌊 SAYOUNG 비즈니스 대시보드")
branch_label = selected_branch if selected_branch != "전체" else "전체 지점"
st.markdown(
    f"**{branch_label}** | {start_d.strftime('%Y.%m.%d')} ~ {end_d.strftime('%Y.%m.%d')} "
    f"*({period_days + 1}일)*"
)
st.divider()

# ── KPI 5개 ───────────────────────────────────────────────────────────────────
kpi = compute_kpi(filtered_df, prev_df)
kpi_keys = list(kpi.keys())
cols = st.columns(5)
for i, col in enumerate(cols):
    label = kpi_keys[i]
    value, delta = kpi[label]
    col.metric(label=label, value=value, delta=delta)

st.divider()

# ── 빠른 요약 차트 ────────────────────────────────────────────────────────────
import plotly.express as px

c1, c2 = st.columns([3, 2])

with c1:
    st.subheader("📈 일별 매출 추이 (전체 지점)")
    day_sales = (
        filtered_df.groupby(["날짜", "지점"])["매출액"].sum().reset_index()
    )
    fig = px.line(
        day_sales, x="날짜", y="매출액", color="지점",
        color_discrete_sequence=["#0077B6", "#00B4D8", "#023E8A"],
        markers=True, line_shape="spline",
    )
    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("🏪 지점별 매출 비중")
    branch_sales = filtered_df.groupby("지점")["매출액"].sum().reset_index()
    fig2 = px.pie(
        branch_sales, values="매출액", names="지점",
        hole=0.45,
        color_discrete_sequence=["#0077B6", "#00B4D8", "#023E8A"],
    )
    fig2.update_traces(textposition="outside", textinfo="percent+label")
    fig2.update_layout(showlegend=False, paper_bgcolor="white")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── 네비게이션 안내 ────────────────────────────────────────────────────────────
st.subheader("📂 상세 분석 페이지")
st.markdown("왼쪽 사이드바에서 원하는 분석 페이지를 선택하세요.")

nc1, nc2, nc3, nc4 = st.columns(4)
nc1.markdown('<div class="nav-card">📈<br>트렌드 분석<br><small>매출·방문자 추이,<br>이동평균, 캔들스틱</small></div>', unsafe_allow_html=True)
nc2.markdown('<div class="nav-card">🥧<br>메뉴 분석<br><small>메뉴 랭킹, 선버스트,<br>시간대 히트맵</small></div>', unsafe_allow_html=True)
nc3.markdown('<div class="nav-card">👥<br>고객 분석<br><small>상관관계, 퍼널,<br>날씨 영향도</small></div>', unsafe_allow_html=True)
nc4.markdown('<div class="nav-card">📋<br>데이터 관리<br><small>목표 설정, 원본 조회,<br>CSV 다운로드</small></div>', unsafe_allow_html=True)
