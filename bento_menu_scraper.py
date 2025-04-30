from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json
import requests
import os

# GASのURLを環境変数から取得
GAS_URL = os.getenv("GAS_URL")
if not GAS_URL:
    raise ValueError("GAS_URL is not set")

# ヘッドレスChrome設定
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.binary_location = "/usr/bin/google-chrome"

# ChromeDriver起動
driver = webdriver.Chrome(options=options)

try:
    driver.get("https://gluseller.com/order/table")
    time.sleep(10)  # ログインを要さないようにする

    # 商品名や価格を含むdivを取得
    items = driver.find_elements(By.CLASS_NAME, "table_menu_item")

    menu_data = []
    for item in items:
        try:
            name = item.find_element(By.CLASS_NAME, "table_menu_name").text.strip()
            price = item.find_element(By.CLASS_NAME, "table_menu_price").text.strip()
            menu_data.append({"name": name, "price": price})
        except Exception as e:
            continue  # skip if any field is missing

    print("== 取得したメニュー一覧 ==")
    print(json.dumps(menu_data, ensure_ascii=False, indent=2))

    # GAS へ POST
    response = requests.post(GAS_URL, json=menu_data)
    response.raise_for_status()
    print("== GAS へ送信成功 ==")

finally:
    driver.quit()
