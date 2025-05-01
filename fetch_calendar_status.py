import os
import json
import time
from datetime import datetime
from collections import defaultdict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Chromeオプション設定
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1280,800")

driver = webdriver.Chrome(options=options)
url = "https://gluseller.com/#top_order"

print("🌐 ページアクセス中...")
driver.get(url)

try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "calendar-date-number"))
    )
    print("✅ calendar-date-number が見つかりました")
    time.sleep(3)
except TimeoutException:
    print("❌ calendar-date-number が見つかりませんでした")
    print(driver.page_source)
    driver.save_screenshot("debug.png")
    driver.quit()
    raise

    # 全 calendar-day セル取得
    cells = driver.find_elements(By.CSS_SELECTOR, "td[class*='calendar-day']")
    print(f"📅 {len(cells)}件のカレンダーセルを検出")

    status_map = defaultdict(lambda: "normal")
    today = datetime.now()

    for cell in cells:
        try:
            date_span = cell.find_element(By.CLASS_NAME, "calendar-date-number")
            day_text = date_span.text.strip()
            if not day_text.isdigit():
                continue
            day = int(day_text)
            date = datetime(today.year, today.month, day).strftime("%Y-%m-%d")

            class_attr = cell.get_attribute("class")
            cell_text = cell.text

            if "calendar-holiday" in class_attr or "休業日" in cell_text:
                status_map[date] = "holiday"
            elif "calendar-premium" in class_attr:
                status_map[date] = "premium"
            elif "calendar-special" in class_attr:
                status_map[date] = "special"
        except Exception as e:
            print(f"⚠️ セル処理スキップ: {e}")
            continue

    # 書き出し先ディレクトリ作成
    os.makedirs("docs", exist_ok=True)

    with open("docs/calendar_status.json", "w", encoding="utf-8") as f:
        json.dump(status_map, f, ensure_ascii=False, indent=2)

    print(f"✅ calendar_status.json を保存しました（{len(status_map)} 件）")

finally:
    driver.quit()
