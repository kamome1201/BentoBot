from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import os
import json
from dotenv import load_dotenv
import time

load_dotenv()
EMAIL = os.getenv("BENTO_EMAIL")
PASSWORD = os.getenv("BENTO_PASSWORD")

options = Options()
options.add_argument("--headless")
options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

driver = webdriver.Chrome(options=options)

try:
    # ログイン
    driver.get("https://gluseller.com/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
    driver.find_element(By.NAME, "email").send_keys(EMAIL)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.TAG_NAME, "button").click()
    time.sleep(5)

    # 注文ページへ移動
    driver.get("https://gluseller.com/#top_order")
    time.sleep(5)

    menu_list = []
    today = datetime.now().strftime("%Y-%m-%d")

    # ✅ 過去の注文履歴（右側）
    items = driver.find_elements(By.CSS_SELECTOR, ".past_total_wrap dt")
    prices = driver.find_elements(By.CSS_SELECTOR, ".past_total_wrap dd")

    for name_el, count_el in zip(items, prices):
        name = name_el.text.strip()
        count = count_el.text.strip()
        menu_list.append({
            "type": "past_order",
            "name": name,
            "count": count,
            "date": today
        })

    # ✅ モーダルのポップアップから商品名と価格を取得（中央ポップアップ）
    time.sleep(2)
    unit_items = driver.find_elements(By.CSS_SELECTOR, "li.unit-item")
    for item in unit_items:
        try:
            name = item.find_element(By.CSS_SELECTOR, ".listOrder__title p").text.strip()
            price = item.find_element(By.CSS_SELECTOR, ".listOrder__price p").text.strip()
            menu_list.append({
                "type": "popup_menu",
                "name": name,
                "price": price,
                "date": today
            })
        except Exception as e:
            print("❌ ポップアップメニュー取得失敗:", e)

    # 保存
    with open("menu_today.json", "w", encoding="utf-8") as f:
        json.dump(menu_list, f, ensure_ascii=False, indent=2)

    print("✅ メニュー取得完了")

finally:
    driver.quit()
