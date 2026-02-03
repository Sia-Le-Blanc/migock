import streamlit as st
import pandas as pd
from database import get_db
from models import RicePrice

# 1. 설정 및 디자인 (부동산114 스타일 유지)
st.set_page_config(page_title="미곡(MIGOCK) 통합 관제", page_icon="🌾", layout="wide")

st.markdown("""
    <style>
        html, body, [class*="css"] { font-family: 'Malgun Gothic', sans-serif; }
        header[data-testid="stHeader"] { border-bottom: 2px solid #004094; }
        div[data-testid="stMetric"], button { border-radius: 0px !important; }
        div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #d1d1d1; }
        div[data-testid="stMetricValue"] { color: #004094; font-weight: 700; }
        .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# 2. 데이터 로드
def load_data():
    db = next(get_db())
    query = db.query(RicePrice).order_by(RicePrice.created_at.desc())
    df = pd.read_sql(query.statement, db.bind)
    db.close()
    return df

# 3. 사이드바 메뉴 (페이지 분기)
st.sidebar.title("MIGOCK System")
page = st.sidebar.radio("메뉴 선택", ["통합 대시보드 (전국)", "🗺️ 지역별 시세 지도"])
st.sidebar.markdown("---")

df = load_data()

# --- 페이지 1: 기존 통합 대시보드 ---
if page == "통합 대시보드 (전국)":
    st.title("🌾 전국 도매 시세 (평균)")
    
    # '전국 평균' 데이터만 필터링
    avg_df = df[df['location'] == '평균']
    
    if not avg_df.empty:
        latest = avg_df.iloc[0]
        # (기존 KPI 및 차트 코드 유지)
        st.metric("오늘의 평균 시세", f"{latest['price']:,}원")
        st.line_chart(avg_df.set_index('created_at')['price'])
        st.dataframe(avg_df, use_container_width=True)
    else:
        st.info("데이터가 없습니다. 크롤러가 곧 수집합니다.")

# --- 페이지 2: 지역별 시세 지도 (NEW!) ---
elif page == "🗺️ 지역별 시세 지도":
    st.title("🗺️ 지역별 실시간 시세 현황")
    
    if not df.empty:
        # 가장 최근 수집된 시간(오늘자)의 데이터만 추출
        latest_time = df.iloc[0]['created_at']
        # 최근 시간과 10분 이내 차이나는 데이터들만(동시간대 수집본)
        latest_df = df[df['created_at'] >= latest_time - pd.Timedelta(minutes=10)].copy()
        
        # '평균' 제외하고 순수 지역만
        local_df = latest_df[latest_df['location'] != '평균']

        # 1. 바 차트로 비교 (비싼 순서대로)
        st.subheader("📊 지역별 가격 순위 (비싼 순)")
        st.bar_chart(local_df.set_index('location')['price'])
        
        # 2. 지도 시각화 (좌표 매핑)
        st.subheader("📍 전국 시세 지도")
        
        # 주요 도시 좌표 하드코딩 (Enterprise급 꼼수)
        coords = {
            "서울": [37.5665, 126.9780], "부산": [35.1796, 129.0756],
            "대구": [35.8714, 128.6014], "인천": [37.4563, 126.7052],
            "광주": [35.1595, 126.8526], "대전": [36.3504, 127.3845],
            "울산": [35.5384, 129.3114], "수원": [37.2636, 127.0286],
            "춘천": [37.8814, 127.7298], "청주": [36.6424, 127.4890],
            "전주": [35.8242, 127.1480], "제주": [33.4996, 126.5312]
        }
        
        # 데이터프레임에 위도/경도 컬럼 추가
        map_data = []
        for idx, row in local_df.iterrows():
            loc = row['location']
            if loc in coords:
                map_data.append({
                    "lat": coords[loc][0],
                    "lon": coords[loc][1],
                    "price": row['price'], # 점 크기로 활용 가능
                    "location": loc
                })
        
        if map_data:
            st.map(pd.DataFrame(map_data), size=2000, zoom=6)
            st.caption("※ 원의 위치는 해당 도매시장의 위치를 나타냅니다.")
        else:
            st.warning("지도에 표시할 지역 데이터가 아직 수집되지 않았습니다.")
            
        # 3. 상세 테이블
        st.dataframe(local_df[['location', 'price', 'created_at']], use_container_width=True)