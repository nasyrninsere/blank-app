import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. 페이지 기본 설정 (반드시 코드 최상단에 위치해야 합니다)
st.set_page_config(
    page_title="SAYOUNG 비즈니스 대시보드", 
    page_icon="🌊", 
    layout="wide", # 화면을 넓게 사용
    initial_sidebar_state="expanded"
)

# 2. 데이터 생성 및 캐싱 (성능 최적화를 위해 캐시 사용)
@st.cache_data
def load_data():
    # 시연을 위한 가상 데이터 생성
    dates = pd.date_range(start="2026-01-01", end="2026-03-18")
    data = pd.DataFrame({
        '날짜': dates,
        '방문자수': np.random.randint(50, 300, size=len(dates)),
        '매출액': np.random.randint(500000, 3000000, size=len(dates)),
        '인기메뉴': np.random.choice(
            ['시그니처 샌드 커피', '아메리카노', '레몬 머랭 파이', '피칸 파이'], 
            size=len(dates)
        ),
        '지점': '광안리 본점'
    })
    return data

df = load_data()

# 3. 사이드바 구성 (필터링 및 제어)
with st.sidebar:
    st.header("⚙️ 대시보드 설정")
    
    # 날짜 범위 선택
    min_date = df['날짜'].min()
    max_date = df['날짜'].max()
    date_range = st.date_input("조회 기간을 선택하세요", [min_date, max_date])
    
    # 메뉴 다중 선택 필터
    unique_menus = df['인기메뉴'].unique()
    selected_menu = st.multiselect("메뉴 필터", unique_menus, default=unique_menus)

# 4. 데이터 필터링 로직
if len(date_range) == 2:
    start_date, end_date = date_range
    # 선택된 날짜와 메뉴에 맞춰 데이터 프레임 필터링
    mask = (
        (df['날짜'].dt.date >= start_date) & 
        (df['날짜'].dt.date <= end_date) & 
        (df['인기메뉴'].isin(selected_menu))
    )
    filtered_df = df[mask]
else:
    filtered_df = df

# 5. 메인 화면 구성
st.title("🌊 SAYOUNG 비즈니스 대시보드")
st.markdown("광안리 본점의 실시간 방문자 및 매출 데이터를 시각화한 대시보드입니다.")
st.divider()

# 6. 핵심 지표 (KPI) - 컬럼 레이아웃 활용
col1, col2, col3 = st.columns(3) # 화면을 3분할

with col1:
    st.metric(
        label="총 방문자수", 
        value=f"{filtered_df['방문자수'].sum():,}명", 
        delta="12%" # 전일/전월 대비 증감률 표현
    )
with col2:
    st.metric(
        label="총 매출액", 
        value=f"₩{filtered_df['매출액'].sum():,}", 
        delta="8%"
    )
with col3:
    st.metric(
        label="일평균 매출", 
        value=f"₩{int(filtered_df['매출액'].mean()):,}", 
        delta="-2%"
    )

st.divider()

# 7. 탭(Tabs)을 활용한 다중 뷰 구성
tab1, tab2, tab3 = st.tabs(["📈 트렌드 분석", "🥧 메뉴별 점유율", "📋 상세 데이터"])

with tab1:
    st.subheader("일자별 매출 추이")
    # Plotly를 사용한 반응형 인터랙티브 차트
    fig_line = px.line(
        filtered_df, 
        x='날짜', 
        y='매출액', 
        markers=True,
        line_shape='spline' # 곡선 형태로 부드럽게 표현
    )
    # use_container_width=True 로 화면 크기에 맞춰 차트 자동 조절
    st.plotly_chart(fig_line, use_container_width=True) 

with tab2:
    st.subheader("인기 메뉴 판매 비중")
    menu_counts = filtered_df['인기메뉴'].value_counts().reset_index()
    menu_counts.columns = ['메뉴', '판매일수']
    
    fig_pie = px.pie(
        menu_counts, 
        values='판매일수', 
        names='메뉴', 
        hole=0.4 # 도넛 형태의 차트
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    st.subheader("상세 데이터 표")
    # 정렬 및 크기 조절이 가능한 인터랙티브 데이터프레임
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
