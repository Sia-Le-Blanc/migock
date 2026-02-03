from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def get_kamis_rice_price():
    # --- 브라우저 설정 ---
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36")

    driver = None
    results = [] # 여러 지역 데이터를 담을 리스트
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        url = "https://www.kamis.or.kr/customer/price/wholesale/item.do"
        driver.get(url)
        time.sleep(3)

        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        
        # 수집할 타겟 지역 목록
        target_regions = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "수원", "춘천", "청주", "전주", "포항", "제주", "평균"]

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            data = [col.text.strip().replace(',', '') for col in cols if col.text.strip()]
            
            if not data: continue

            region = data[0]
            price = 0
            
            # 1. '평균'인 경우 (데이터 구조: ['평균', '가격', ...])
            if region == "평균" and len(data) > 1:
                price = data[1]
                
            # 2. 지역인 경우 (데이터 구조: ['서울', '20kg', '가격', ...]) -> 인덱스 2번이 가격
            elif region in target_regions and len(data) > 2:
                price = data[2]
            
            # 가격이 숫자인지 확인하고 리스트에 추가
            if str(price).isdigit():
                results.append({
                    "item_name": "쌀(일반계/20kg/상품)",
                    "price": int(price),
                    "location": region
                })

        return {"status": "success", "data": results}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    print(get_kamis_rice_price())