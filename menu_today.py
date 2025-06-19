import os
import json
import unicodedata
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv
from shutil import which
import time
from pathlib import Path
from shutil import which

def normalize(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    return text.replace("\n", "").replace("　", " ").strip()

# .env から認証情報取得
load_dotenv()
EMAIL = os.getenv("BENTO_EMAIL")
PASSWORD = os.getenv("BENTO_PASSWORD")

# Chromeヘッドレス設定
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Chrome パスを自動検出
chrome_path = which("google-chrome")
mac_chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if chrome_path:
    options.binary_location = chrome_path
elif Path(mac_chrome_path).exists():
    options.binary_location = mac_chrome_path

driver = webdriver.Chrome(options=options)

today = datetime.now()
today_day = today.day
today_str = today.strftime("%Y-%m-%d")
menu_list = []

try:
    # ログイン
    driver.get("https://gluseller.com/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
    driver.find_element(By.NAME, "email").send_keys(EMAIL)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # 注文ページへ
    driver.get("https://gluseller.com/#top_order")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "calendar")))
    time.sleep(2)

    # 今日の日付をクリック
    clicked = False
    cells = driver.find_elements(By.CSS_SELECTOR, "td.calendar-enable")
    for cell in cells:
        try:
            if "calendar-holiday" in cell.get_attribute("class"):
                continue
            span = cell.find_element(By.CLASS_NAME, "calendar-date-number")
            if int(span.text.strip()) == today_day:
                driver.execute_script("arguments[0].click();", cell)
                clicked = True
                break
        except:
            continue

    time.sleep(2)

    if clicked:
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "modaal-content-container")))
            time.sleep(2)
            modal = driver.find_element(By.CLASS_NAME, "modaal-wrapper")
            items = modal.find_elements(By.CSS_SELECTOR, "li.unit-item")
            for item in items:
                try:
                    name = item.find_element(By.CLASS_NAME, "listOrder__title").text.strip()
                    price = item.find_element(By.CLASS_NAME, "listOrder__price").text.strip()
                    menu_list.append({
                        "type": "popup_menu",
                        "name": normalize(name),
                        "price": price,
                        "date": today_str
                    })
                except Exception as e:
                    print("❌ メニュー取得失敗:", e)
        except Exception as e:
            print("⚠️ モーダルが表示されません:", e)

    # フォールバック（ページ全体）
    if not menu_list:
        try:
            driver.get("https://gluseller.com/order")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "post_total_wrap")))
            items = driver.find_elements(By.CSS_SELECTOR, "div.d-flex.justify-content-between.align-items-stretch")
            for item in items:
                try:
                    name = item.find_element(By.TAG_NAME, "dt").text.strip()
                    price = item.find_element(By.TAG_NAME, "dd").text.strip()
                    menu_list.append({
                        "type": "backup_menu",
                        "name": normalize(name),
                        "price": price,
                        "date": today_str
                    })
                except Exception as e:
                    print("⚠️ バックアップメニュー取得失敗:", e)
        except Exception as e:
            print("❌ バックアップページアクセス失敗:", e)

    # 固定メニューの読み込み
    fixed_menu_path = "static/fixed_menu.json"
    if os.path.exists(fixed_menu_path):
        with open(fixed_menu_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                item["type"] = "fixed_menu"
                item["date"] = today_str
                menu_list.append(item)

    # 保存
    os.makedirs("static", exist_ok=True)
    with open("static/menu_today.json", "w", encoding="utf-8") as f:
        json.dump(menu_list, f, ensure_ascii=False, indent=2)
    print("✅ menu_today.json を保存しました（件数:", len(menu_list), "）")

finally:
    driver.quit()
