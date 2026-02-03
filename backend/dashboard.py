import streamlit as st
import pandas as pd
import altair as alt
from database import get_db
from models import RicePrice

# 1. 페이지 설정
st.set_page_config(page_title="MIGOCK 지역별 시세", page_icon="🌾", layout="wide")

st.markdown("""
    <style>
        html, body, [class*="css"] { font-family: 'Malgun Gothic', sans-serif; }
        header[data-testid="stHeader"] { border-bottom: 2px solid #004094; }
        .block-container { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# 2. 데이터 로드 및 "강력한" 정제
def load_data():
    db = next(get_db())
    query = db.query(RicePrice).order_by(RicePrice.created_at.desc())
    df = pd.read_sql(query.statement, db.bind)
    db.close()
    
    if df.empty: return pd.DataFrame(), 0

    # (1) 화이트리스트 필터링
    VALID_REGIONS = [
        "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
        "수원", "춘천", "청주", "전주", "포항", "제주", "순천", "안동", "창원", 
        "평균"
    ]
    
    # 공백 제거 후 필터링 (가장 흔한 실수 방지)
    df['location'] = df['location'].astype(str).str.strip()
    clean_df = df[df['location'].isin(VALID_REGIONS)].copy()
    
    if clean_df.empty: return pd.DataFrame(), 0

    # (2) [핵심] 가격 데이터 강제 정수 변환 (에러 방지) ⭐
    clean_df['price'] = pd.to_numeric(clean_df['price'], errors='coerce').fillna(0).astype(int)

    # (3) 최근 데이터 추출
    latest_timestamp = clean_df.iloc[0]['created_at']
    recent_df = clean_df[clean_df['created_at'] >= latest_timestamp - pd.Timedelta(minutes=10)].copy()
    
    # (4) 중복 제거
    unique_df = recent_df.sort_values('created_at', ascending=False).drop_duplicates(subset=['location'])
    
    # (5) 평균값 계산
    avg_row = unique_df[unique_df['location'] == '평균']
    avg_price = avg_row.iloc[0]['price'] if not avg_row.empty else 0
    
    # (6) 지역 데이터만 남김
    local_df = unique_df[unique_df['location'] != '평균'].copy()
    
    return local_df, avg_price

# --- 메인 화면 ---
st.title("📊 지역별 쌀 시세 랭킹")
st.markdown("---")

df, avg_price = load_data()

if not df.empty:
    # A. 상단 KPI
    col1, col2, col3 = st.columns(3)
    
    max_row = df.loc[df['price'].idxmax()]
    min_row = df.loc[df['price'].idxmin()]

    col1.metric("전국 평균", f"{avg_price:,}원")
    col2.metric("최고가 지역", f"{max_row['location']}", f"{max_row['price']:,}원")
    col3.metric("최저가 지역", f"{min_row['location']}", f"{min_row['price']:,}원")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # B. 막대그래프 (안정성 강화 버전)
    st.subheader("🏆 가격 높은 순 랭킹 (실시간)")
    
    # 색상 설정
    df['color'] = df['price'].apply(lambda x: '#FF4B4B' if x > avg_price else '#1C83E1')
    
    # [핵심] Y축 범위 자동 보정 (안전장치)
    # 데이터가 1개뿐이거나 가격이 다 똑같을 때 그래프가 깨지는 걸 방지합니다.
    p_min = df['price'].min()
    p_max = df['price'].max()
    
    if p_min == p_max: # 가격이 다 똑같으면?
        y_domain = [p_min - 500, p_max + 500]
    else:
        y_domain = [p_min - 500, p_max + 1000]

    # 1. 기본 차트
    base = alt.Chart(df).encode(
        # X축: 지역명 (가나다순이 아니라 가격순 정렬 '-y')
        x=alt.X('location', sort='-y', title=None, axis=alt.Axis(labelAngle=0, labelFontSize=12)),
        # Y축: 가격 (Auto Scale 적용)
        y=alt.Y('price', title='도매가격(원)', scale=alt.Scale(domain=y_domain))
    )

    # 2. 막대 (Bars)
    bars = base.mark_bar().encode(
        color=alt.Color('color', scale=None),
        tooltip=['location', 'price']
    )

    # 3. 텍스트 (Labels)
    text = base.mark_text(
        dy=-10, # 막대 위로 10픽셀 띄우기
        fontSize=12,
        fontWeight='bold'
    ).encode(
        text=alt.Text('price', format=',')
    )

    # 4. 합체
    chart = alt.layer(bars, text).properties(height=450)
    st.altair_chart(chart, use_container_width=True)

    # C. 데이터 확인용 (디버깅)
    with st.expander("🔍 데이터가 제대로 들어왔는지 확인하기"):
        st.write("아래 표에 '가격'이 숫자로 잘 보이는지 확인하세요.")
        st.dataframe(df[['location', 'price', 'created_at']], use_container_width=True)

else:
    st.error("❌ 표시할 데이터가 없습니다.")
    st.info("데이터베이스에 '서울', '부산' 같은 지역 데이터가 저장되어 있는지 확인해주세요.")