from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from dotenv import load_dotenv
import os
import json
import time

# ロード環境変数
load_dotenv()
EMAIL = os.getenv("BENTO_EMAIL")
PASSWORD = os.getenv("BENTO_PASSWORD")

# Selenium設定
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

try:
    # ログイン処理後
    driver.find_element(By.TAG_NAME, "button").click()
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".page_contents"))
    )
    
    # 注文ページに遷移（任意、または省略）
    driver.get("https://gluseller.com/#top_order")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".post_total_wrap dt"))
    )

    # メニュー抽出
    today_str = datetime.now().strftime("%Y-%m-%d")
    menu_list = []

    menu_blocks = driver.find_elements(By.CSS_SELECTOR, ".post_total_wrap .d-flex.justify-content-between.align-items-stretch")
    for block in menu_blocks:
        try:
            name = block.find_element(By.TAG_NAME, "dt").text.strip()
            price = block.find_element(By.TAG_NAME, "dd").text.strip()
            if name and price:
                menu_list.append({
                    "type": "popup_menu",
                    "name": name,
                    "price": price,
                    "date": today_str
                })
        except:
            continue

    with open("docs/menu_today.json", "w", encoding="utf-8") as f:
        json.dump(menu_list, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(menu_list)}件のメニューを保存しました")

finally:
    driver.quit()
