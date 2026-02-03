from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

class RicePrice(Base):
    # 1. DB에 저장될 테이블 이름
    __tablename__ = "rice_prices"

    # 2. 컬럼(칸) 정의
    id = Column(Integer, primary_key=True, index=True)  # 고유 번호 (1, 2, 3...)
    price = Column(Integer, nullable=False)             # 가격 (59720)
    item_name = Column(String, nullable=False)          # 품목명 (쌀 20kg 상품)
    location = Column(String, default="National")       # 지역 (전국 평균)
    
    # 수집 날짜 (자동으로 현재 시간 입력됨)
    created_at = Column(DateTime(timezone=True), server_default=func.now())