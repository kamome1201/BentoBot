from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from shutil import which
import os
import json
from dotenv import load_dotenv
import time

# 環境変数の読み込み
load_dotenv()
EMAIL = os.getenv("BENTO_EMAIL")
PASSWORD = os.getenv("BENTO_PASSWORD")

# Chromeヘッドレス設定
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.binary_location = which("google-chrome")

driver = webdriver.Chrome(options=options)

try:
    # ログイン
    driver.get("https://gluseller.com/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
    driver.find_element(By.NAME, "email").send_keys(EMAIL)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "top_order")))

    # 注文ページへ移動
    driver.get("https://gluseller.com/#top_order")
    time.sleep(3)

    today = datetime.now()
    today_day = today.day
    today_str = today.strftime("%Y-%m-%d")

    # カレンダークリック試行
    clicked = False
    calendar_cells = driver.find_elements(By.CSS_SELECTOR, "td.calendar-enable")
    for cell in calendar_cells:
        try:
            if "calendar-holiday" in cell.get_attribute("class"):
                continue
            span = cell.find_element(By.CLASS_NAME, "calendar-date-number")
            if int(span.text.strip()) == today_day:
                cell.click()
                clicked = True
                break
        except:
            continue

    menu_list = []

    if clicked:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.listOrder li.unit-item"))
            )
            unit_items = driver.find_elements(By.CSS_SELECTOR, "ul.listOrder li.unit-item")
            for item in unit_items:
                try:
                    name = item.find_element(By.CSS_SELECTOR, ".listOrder__title p").text.strip()
                    price = item.find_element(By.CSS_SELECTOR, ".listOrder__price p").text.strip()
                    menu_list.append({
                        "type": "popup_menu",
                        "name": name,
                        "price": price,
                        "date": today_str
                    })
                except Exception as e:
                    print("❌ メニュー取得失敗:", e)
        except TimeoutException:
            print("⚠️ モーダルが表示されませんでした。休業日かもしれません。")

    # フォールバック: メニュー一覧を直接取得
    if not menu_list:
        try:
            driver.get("https://gluseller.com/order")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "post_total_wrap")))
            items = driver.find_elements(By.CSS_SELECTOR, "div.d-flex.justify-content-between.align-items-stretch")
            for item in items:
                try:
                    name = item.find_element(By.TAG_NAME, "dt").text.strip()
                    price = item.find_element(By.TAG_NAME, "dd").text.strip()
                    if name and price:
                        menu_list.append({
                            "type": "popup_menu",
                            "name": name,
                            "price": price,
                            "date": today_str
                        })
                except Exception as e:
                    print("⚠️ バックアップメニュー取得失敗:", e)
        except Exception as e:
            print("❌ バックアップページアクセス失敗:", e)

    # JSON保存
    os.makedirs("docs", exist_ok=True)
    with open("docs/menu_today.json", "w", encoding="utf-8") as f:
        json.dump(menu_list, f, ensure_ascii=False, indent=2)

    print("✅ menu_today.json を保存しました（件数:", len(menu_list), "）")

finally:
    driver.quit()
