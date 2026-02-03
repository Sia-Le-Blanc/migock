from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
import database
import models
import crawler
import datetime

# --- [핵심] 1. 자동 수집 로직 (스케줄러가 할 일) ---
# 기존 함수를 이걸로 교체하세요
def auto_collect_rice_price():
    print(f"⏰ [자동 수집] {datetime.datetime.now()} - 지역별 시세를 긁어옵니다...")
    
    result = crawler.get_kamis_rice_price()
    
    if result['status'] == 'success':
        db = database.SessionLocal()
        try:
            count = 0
            # 리스트에 있는 모든 지역 데이터 저장
            for item in result['data']:
                new_price = models.RicePrice(
                    item_name=item['item_name'],
                    price=item['price'],
                    location=item['location']
                )
                db.add(new_price)
                count += 1
            
            db.commit()
            print(f"✅ [저장 완료] 총 {count}개 지역 데이터 확보!")
            
        except Exception as e:
            print(f"❌ [DB 에러] {e}")
            db.rollback()
        finally:
            db.close()
    else:
        print(f"⚠️ [수집 실패] {result.get('message')}")

# --- [설정] 2. 서버 수명주기 관리 (켜질 때 스케줄러 시작) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 켜질 때 실행
    print("🚀 서버 가동! 스케줄러를 시작합니다.")
    
    scheduler = BackgroundScheduler()
    
    # [중요] 테스트용: 1분마다 실행 (나중엔 'cron'으로 매일 아침으로 바꿀 예정)
    scheduler.add_job(auto_collect_rice_price, 'interval', minutes=1, id='rice_job')
    
    scheduler.start()
    
    yield # 여기서 서버가 계속 돌아감
    
    # 서버 꺼질 때 실행
    print("💤 서버 종료. 스케줄러도 끕니다.")
    scheduler.shutdown()

# --- 3. FastAPI 앱 설정 ---
models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(lifespan=lifespan) # 수명주기(lifespan) 등록

# --- API 라우터 ---
@app.get("/")
def read_root():
    return {"message": "MIGOCK Platform with Scheduler 🕰️"}

# 수동 수집 버튼 (비상용)
@app.get("/collect/rice")
def collect_rice_manual(db: Session = Depends(database.get_db)):
    auto_collect_rice_price() # 위의 함수 재활용
    return {"message": "수동 수집 명령을 보냈습니다. 서버 로그를 확인하세요."}

# 데이터 조회
@app.get("/rice/history")
def get_rice_history(db: Session = Depends(database.get_db)):
    results = db.query(models.RicePrice).order_by(models.RicePrice.created_at.desc()).all()
    return {"count": len(results), "history": results}