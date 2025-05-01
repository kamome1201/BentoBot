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

from dotenv import load_dotenv

# .env or GitHub Secrets を読み込み
load_dotenv()
EMAIL = os.getenv("BENTO_EMAIL")
PASSWORD = os.getenv("BENTO_PASSWORD")

# Chromeオプション設定
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1280,800")

driver = webdriver.Chrome(options=options)

try:
    # 🔐 ログイン処理
    print("🔐 ログインページへアクセス中...")
    driver.get("https://gluseller.com/login")

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
    driver.find_element(By.NAME, "email").send_keys(EMAIL)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.TAG_NAME, "button").click()

    print("✅ ログイン完了。注文ページへ遷移中...")
    time.sleep(3)

    # 📅 注文カレンダー表示ページへ遷移
    driver.get("https://gluseller.com/#top_order")

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "calendar-date-number"))
    )
    print("✅ カレンダーが表示されました")
    time.sleep(2)

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

            if "calendar-holiday" in class_attr o_
