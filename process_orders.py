import os
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()
GITHUB_TOKEN = os.getenv("GH_TOKEN")
REPO = "kamome1201/BentoBot"
ISSUES_URL = f"https://api.github.com/repos/{REPO}/issues"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def parse_issue(issue):
    body = issue.get("body", "")
    date_match = re.search(r"【注文日】\s*(\d{4}-\d{2}-\d{2})", body)
    orders = re.findall(r"-\s*(.+?)\s*×\s*(\d+)", body)
    if not date_match:
        return None
    return {
        "number": issue["number"],
        "date": date_match.group(1),
        "orders": [{"name": name.strip(), "count": int(qty)} for name, qty in orders]
    }

def fetch_pending_issues():
    res = requests.get(f"{ISSUES_URL}?state=open&labels=bento-order", headers=HEADERS)
    if res.status_code != 200:
        print(f"❌ GitHub API エラー: {res.status_code} - {res.text}")
        return []
    issues = res.json()
    pending = []
    for issue in issues:
        if not any(label["name"] == "ordered" for label in issue.get("labels", [])):
            parsed = parse_issue(issue)
            if parsed:
                pending.append(parsed)
    return pending

def mark_issue_as_ordered(issue_number):
    url = f"{ISSUES_URL}/{issue_number}"
    res = requests.patch(url, headers=HEADERS, json={"labels": ["bento-order", "ordered"]})
    if res.status_code == 200:
        print(f"✅ Issue #{issue_number} に 'ordered' ラベルを追加しました。")
    else:
        print(f"❌ Issue 更新失敗: {res.text}")

def perform_order(order_info):
    email = os.getenv("BENTO_EMAIL")
    password = os.getenv("BENTO_PASSWORD")
    date_str = order_info["date"]

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    try:
        # ログイン
        driver.get("https://gluseller.com/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        driver.find_element(By.NAME, "email").send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # 注文画面へ明示遷移
        driver.get("https://gluseller.com/#top_order")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "calendar")))
        print("✅ 注文ページへ遷移しました")
        
        # 日付選択
        day_number = int(date_str.split("-")[2])
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "td.calendar-enable")))
        cells = driver.find_elements(By.CSS_SELECTOR, "td.calendar-enable")
        for cell in cells:
            try:
                span_text = cell.find_element(By.CLASS_NAME, "calendar-date-number").text.strip()
                print(f"検査中: {span_text}")
                if span_text == str(day_number):
                    cell.click()
                    print(f"✅ {day_number}日 を選択")
                    break
            except Exception as e:
                continue
        else:
            print("❌ 日付クリック失敗")
            return False

        # 数量入力
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.unit-item")))
        items = driver.find_elements(By.CSS_SELECTOR, "li.unit-item")
        for item in items:
            try:
                name_el = item.find_element(By.CSS_SELECTOR, "div.listOrder__title > span")
                bento_name = name_el.text.strip()
                for order in order_info["orders"]:
                    if bento_name == order["name"]:
                        input_el = item.find_element(By.CSS_SELECTOR, "input.input-quantity")
                        input_el.clear()
                        input_el.send_keys(str(order["count"]))
                        print(f"✅ {bento_name} ← {order['count']}個")
            except Exception as e:
                print(f"⚠️ 入力失敗: {e}")
                continue

        # 注文を決定
        order_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "cart__submit")))
        order_btn.click()
        print("✅ 注文を決定ボタンをクリック")

        return True

    except Exception as e:
        print(f"❌ 注文エラー: {e}")
        return False

    finally:
        driver.quit()

if __name__ == "__main__":
    issues = fetch_pending_issues()
    for issue in issues:
        if perform_order(issue):
            mark_issue_as_ordered(issue["number"])
