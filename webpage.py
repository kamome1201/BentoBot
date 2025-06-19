from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import requests
import json
import time

app = Flask(__name__)

ORDERS_FILE = "static/orders.json"
MENU_FILE = "static/menu_today.json"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("REPO", "kamome1201/BentoBot")
ISSUES_URL = f"https://api.github.com/repos/{REPO}/issues"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def load_menu():
    if os.path.exists(MENU_FILE):
        with open(MENU_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def append_order_to_json(order_data):
    """orders.jsonに注文データを追記保存"""
    orders = []
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            orders = json.load(f)
    orders.append(order_data)
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

def get_web_menu_names():
    """web注文対象のメニュー名セットを取得（固定メニュー以外）"""
    with open(MENU_FILE, encoding="utf-8") as f:
        menu = json.load(f)
    return set(item["name"] for item in menu if item.get("type") != "fixed_menu")

def is_web_menu(name):
    """メニュー名がWeb注文対象かどうか判定"""
    web_menu_names = get_web_menu_names()
    return name in web_menu_names

def perform_web_order(orders, order_date, user_name):
    EMAIL = os.getenv("BENTO_EMAIL")
    PASSWORD = os.getenv("BENTO_PASSWORD")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    try:
        # 1. ログイン
        driver.get("https://gluseller.com/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        driver.find_element(By.NAME, "email").send_keys(EMAIL)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # 2. 注文ページへ
        driver.get("https://gluseller.com/#top_order")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "calendar")))
        time.sleep(2)

        # 3. 注文日カレンダーから該当日をクリック
        clicked = False
        cells = driver.find_elements(By.CSS_SELECTOR, "td.calendar-enable")
        target_day = int(order_date.split("-")[2])
        for cell in cells:
            try:
                if "calendar-holiday" in cell.get_attribute("class"):
                    continue
                span = cell.find_element(By.CLASS_NAME, "calendar-date-number")
                if int(span.text.strip()) == target_day:
                    driver.execute_script("arguments[0].click();", cell)
                    clicked = True
                    break
            except:
                continue
        if not clicked:
            return False, f"注文日 {order_date} が選択できませんでした"

        time.sleep(2)

        # 4. 各商品を注文
        for order in orders:
            ordered = False
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "modaal-content-container")))
                time.sleep(2)
                modal = driver.find_element(By.CLASS_NAME, "modaal-wrapper")
                items = modal.find_elements(By.CSS_SELECTOR, "li.unit-item")
                for item in items:
                    name = item.find_element(By.CLASS_NAME, "listOrder__title").text.strip()
                    if order['name'] in name:
                        # 数量指定
                        count_input = item.find_element(By.CLASS_NAME, "listOrder__input")
                        count_input.clear()
                        count_input.send_keys(str(order['count']))
                        # 注文ボタン押す
                        item.find_element(By.TAG_NAME, "button").click()
                        time.sleep(1)
                        # ポップアップなどで失敗検知
                        if detect_order_failure(driver):
                            return False, f"注文失敗（{name}）: 締め切りまたは材料切れ"
                        ordered = True
                        break
                if not ordered:
                    return False, f"{order['name']} の注文項目が見つかりませんでした"
            except Exception as e:
                return False, f"注文エラー: {str(e)}"

        return True, ""  # 全注文成功

    except Exception as e:
        return False, str(e)
    finally:
        driver.quit()

def detect_order_failure(driver):
    """ポップアップやエラー表示で注文失敗を検出（例：'締め切られている'など）"""
    try:
        # 例：エラーメッセージが画面に出ているか検出
        # driver.page_source で'締め切られている'や'登録できません'などを検出
        if "締め切られている" in driver.page_source or "登録できません" in driver.page_source:
            return True
        return False
    except:
        return False

def create_or_find_issue(order_data):
    """
    注文日＋注文者でIssueを検索し、なければ新規作成してIssue番号を返す
    """
    order_date = order_data["order_date"]
    name = order_data.get("name", "unknown")

    # 検索（openなbento-orderラベルIssueの中から注文者と注文日で絞る）
    q = f"{ISSUES_URL}?state=open&labels=bento-order"
    r = requests.get(q, headers=HEADERS)
    if r.status_code == 200:
        for issue in r.json():
            if (f"【注文者】{name}" in issue.get("body", "")) and (f"【注文日】{order_date}" in issue.get("body", "")):
                return issue["number"]

    # なければ新規作成
    title = f"お弁当注文 - {name} - {order_date}"
    body = f"【注文者】{name}\n【注文日】{order_date}\n\n【注文内容】\n"
    for order in order_data["orders"]:
        body += f"- {order['name']} × {order['count']}\n"
    data = {"title": title, "body": body, "labels": ["bento-order"]}
    r = requests.post(ISSUES_URL, headers=HEADERS, json=data)
    if r.status_code == 201:
        return r.json()["number"]
    else:
        raise Exception(f"Issue作成失敗: {r.text}")

def post_order_failed_comment(issue_number, msg):
    url = f"{ISSUES_URL}/{issue_number}/comments"
    body = f"❌ 注文処理失敗: {msg}"
    requests.post(url, headers=HEADERS, json={"body": body})

def add_issue_label(issue_number, label):
    url = f"{ISSUES_URL}/{issue_number}/labels"
    requests.post(url, headers=HEADERS, json={"labels": [label]})

@app.route('/order')
def order_form():
    return render_template("order.html")

@app.route('/submit', methods=['POST'])
def submit_order():
    data = request.get_json()
    append_order_to_json(data)
    web_orders = [o for o in data["orders"] if is_web_menu(o["name"])]
    if web_orders:
        ok, msg = perform_web_order(web_orders, data["order_date"], data.get("name", ""))
        if not ok:
            issue_number = create_or_find_issue(data)
            post_order_failed_comment(issue_number, msg)
            add_issue_label(issue_number, "order-failed")
            return jsonify({"status": "error", "msg": msg})
    return jsonify({"status": "ok"})

@app.route('/summary')
def summary():
    orders = load_orders()
    # 日付ごとの注文一覧・合計金額集計
    summary = {}
    menu = load_menu()
    price_map = {item["name"]: int(item.get("price", "0").replace("円", "").replace("yen", "")) for item in menu}

    for order in orders:
        date = order["order_date"]
        if date not in summary:
            summary[date] = {"orders": [], "total": 0}
        for o in order["orders"]:
            summary[date]["orders"].append({
                "name": o["name"],
                "count": int(o["count"])
            })
            # 金額計算
            price = price_map.get(o["name"], 0)
            summary[date]["total"] += price * int(o["count"])

    # ソート（日付降順）
    sorted_dates = sorted(summary.keys(), reverse=True)
    return render_template("summary.html", summary=summary, sorted_dates=sorted_dates)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
