import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. 페이지 기본 설정 (반드시 코드 최상단에 위치해야 합니다)
st.set_page_config(
    page_title="고도화된 비즈니스 대시보드",
    page_icon="📈",
    layout="wide", # 반응형 넓은 화면 사용
    initial_sidebar_state="expanded"
)

# 2. 데이터 로딩 및 캐싱 (성능 최적화)
@st.cache_data
def load_mock_data():
    """가상의 비즈니스 데이터를 생성하고 캐싱하여 매번 재연산하지 않도록 합니다."""
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=100)
    df = pd.DataFrame({
        '날짜': dates,
        '매출액': np.random.randint(1000000, 5000000, size=100),
        '방문자수': np.random.randint(500, 3000, size=100),
        '카테고리': np.random.choice(['전자제품', '의류', '식품'], size=100),
        '고객만족도': np.random.uniform(3.0, 5.0, size=100)
    })
    return df

df = load_mock_data()

# 3. 세션 상태 (Session State) 관리
# 사용자가 버튼을 누르거나 필터를 바꿔도 특정 데이터를 기억하게 합니다.
if 'refresh_count' not in st.session_state:
    st.session_state['refresh_count'] = 0

# 4. 사이드바 (사이드 패널) 구성
with st.sidebar:
    st.header("⚙️ 대시보드 제어판")
    st.caption("데이터를 원하는 조건으로 필터링하세요.")
    
    # 데이터 필터 인터페이스
    selected_categories = st.multiselect(
        "카테고리 선택",
        options=df['카테고리'].unique(),
        default=df['카테고리'].unique()
    )
    
    date_range = st.date_input(
        "날짜 범위 지정",
        value=[df['날짜'].min(), df['날짜'].max()],
        min_value=df['날짜'].min(),
        max_value=df['날짜'].max()
    )
    
    st.divider()
    
    # 상태 관리 테스트용 버튼
    if st.button("🔄 데이터 수동 새로고침"):
        st.session_state['refresh_count'] += 1
        st.rerun() # 화면 즉시 강제 새로고침

# 날짜 범위 예외 처리 (사용자가 날짜를 하나만 선택했을 때 에러 방지)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0]

# 필터가 적용된 데이터프레임 생성
filtered_df = df[
    (df['카테고리'].isin(selected_categories)) &
    (df['날짜'] >= pd.to_datetime(start_date)) &
    (df['날짜'] <= pd.to_datetime(end_date))
]

# 5. 메인 레이아웃 및 헤더
st.title("📈 주간 비즈니스 성과 대시보드")
st.markdown(f"**현재 설정된 필터 조건으로 분석된 데이터입니다.** (새로고침 횟수: {st.session_state['refresh_count']}회)")

# 탭(Tab)으로 화면 분할하여 복잡도 줄이기
tab1, tab2, tab3 = st.tabs(["📊 주요 지표 및 차트", "📋 데이터 테이블", "💡 추가 인사이트"])

with tab1:
    # 6. 핵심 지표 (Metrics) - Columns 레이아웃 활용
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="총 매출액", value=f"{filtered_df['매출액'].sum():,}원", delta="12% (전월비)")
    with col2:
        st.metric(label="총 방문자 수", value=f"{filtered_df['방문자수'].sum():,}명", delta="-3%", delta_color="inverse")
    with col3:
        st.metric(label="평균 고객만족도", value=f"{filtered_df['고객만족도'].mean():.2f}점", delta="0.5점")
    with col4:
        st.metric(label="검색된 데이터 수", value=f"{len(filtered_df)}건")

    st.divider()

    # 7. 인터랙티브 반응형 차트 (Plotly 연동)
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("일자별 매출 추이")
        # Plotly를 활용한 라인 차트
        fig_line = px.line(
            filtered_df, x='날짜', y='매출액', color='카테고리',
            template='plotly_white', markers=True
        )
        # use_container_width=True 로 설정해야 브라우저 창 크기에 맞춰 차트가 늘어나고 줄어듭니다.
        st.plotly_chart(fig_line, use_container_width=True)

    with chart_col2:
        st.subheader("카테고리별 방문자 비율")
        # Plotly를 활용한 도넛 차트
        fig_pie = px.pie(
            filtered_df, names='카테고리', values='방문자수',
            hole=0.4, template='plotly_white'
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.subheader("원본 데이터 탐색")
    
    # 8. 대화형 데이터프레임 및 다운로드
    # st.dataframe은 컬럼 정렬, 크기 조절 등을 기본 지원합니다.
    st.dataframe(
        filtered_df.style.highlight_max(subset=['매출액', '방문자수'], color='lightgreen'),
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # 필터링된 데이터를 CSV로 다운로드하는 기능
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 현재 데이터 CSV로 다운로드",
        data=csv_data,
        file_name='filtered_dashboard_data.csv',
        mime='text/csv'
    )

with tab3:
    st.subheader("대시보드 사용 가이드")
    
    # 9. 확장 패널 (Expander) - 부가적인 텍스트를 숨겨두어 화면을 깔끔하게 유지
    with st.expander("📌 데이터 분석 팁 펼쳐보기"):
        st.markdown("""
        * **사이드바 활용:** 좌측 사이드바에서 카테고리와 날짜를 조정하면 즉각적으로 우측의 지표와 차트가 다시 계산됩니다.
        * **반응형 차트:** 차트의 특정 범례를 클릭하면 해당 카테고리만 끄거나 켤 수 있습니다. (Plotly 기본 기능)
        * **다운로드:** [데이터 테이블] 탭에서 현재 분석 중인 데이터만 엑셀(CSV) 파일로 저장해 보고서에 활용하세요.
        """)
