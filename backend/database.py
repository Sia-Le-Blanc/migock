from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. DB 접속 정보 (가장 중요!)
# 형식: postgresql://아이디:비번@주소:포트/데이터베이스이름
# * 설치할 때 비번을 migock1234로 하셨다면 그대로 두시고, 다르면 꼭 수정하세요!
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:1234@localhost:5432/postgres"

# 2. 엔진 시동 (커넥션 풀 생성)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. 세션 공장 (데이터를 사고 팔 때마다 여기서 세션을 하나씩 빌려감)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 모델들의 조상님 (이 클래스를 상속받아야 DB 테이블이 됨)
Base = declarative_base()

# 5. 접속 테스트용 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()