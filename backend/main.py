from fastapi import FastAPI

app = FastAPI()

# 1. 서버 생존 신고 (Health Check)
@app.get("/")
def read_root():
    return {
        "platform": "Korea Rice Exchange (KRX)",
        "status": "Alive",
        "target": "Private Sector 30%" 
    }

# 2. 가짜 시세 데이터 (테스트용)
@app.get("/price")
def get_fake_price():
    return {
        "date": "2026-02-03",
        "price": 48500,
        "location": "전남 나주"
    }