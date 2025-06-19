
import os
import re
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import unicodedata

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "kamome1201/BentoBot"
ISSUES_URL = f"https://api.github.com/repos/{REPO}/issues"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def normalize(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    return text.replace("\n", "").replace("　", " ").strip()

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
    return [parse_issue(issue) for issue in issues if parse_issue(issue) and not any(label["name"] == "ordered" for label in issue.get("labels", []))]

def mark_issue_as_ordered(issue_number):
    url = f"{ISSUES_URL}/{issue_number}"
    res = requests.patch(url, headers=HEADERS, json={"labels": ["bento-order", "ordered"]})
    if res.status_code == 200:
        print(f"✅ Issue #{issue_number} に 'ordered' ラベルを追加しました。")
    else:
        print(f"❌ Issue 更新失敗: {res.text}")

def mark_issue_as_failed(issue_number):
    url = f"{ISSUES_URL}/{issue_number}"
    res = requests.patch(url, headers=HEADERS, json={"labels": ["bento-order", "order-failed"]})
    if res.status_code == 200:
        print(f"⚠️ Issue #{issue_number} に 'order-failed' ラベルを追加しました。")
    else:
        print(f"❌ ラベル更新失敗: {res.text}")

def comment_on_issue(issue_number, message):
    url = f"{ISSUES_URL}/{issue_number}/comments"
    res = requests.post(url, headers=HEADERS, json={"body": message})
    if res.status_code == 201:
        print(f"📝 Issue #{issue_number} にコメントしました。")
    else:
        print(f"❌ コメント失敗: {res.text}")

def perform_order(order_info):
    email = os.getenv("BENTO_EMAIL")
    password = os.getenv("BENTO_PASSWORD")
    date_str = order_info["date"]
    day_number = int(date_str.split("-")[2])

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://gluseller.com/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        driver.find_element(By.NAME, "email").send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        driver.get("https://gluseller.com/#top_order")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "calendar")))

        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "td.calendar-enable")))
        cells = driver.find_elements(By.CSS_SELECTOR, "td.calendar-enable")
        target_cell = None
        for cell in cells:
            try:
                if "calendar-holiday" in cell.get_attribute("class") or "calendar-null" in cell.get_attribute("class"):
                    continue
                if cell.find_element(By.CLASS_NAME, "calendar-date-number").text.strip() == str(day_number):
                    target_cell = cell
                    break
            except:
                continue

        if not target_cell:
            print(f"❌ {date_str} の注文可能セルが見つかりません")
            return False

        driver.execute_script("arguments[0].click();", target_cell)
        time.sleep(2)

        WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CLASS_NAME, "modaal-content-container")))
        modal = driver.find_element(By.CLASS_NAME, "modaal-wrapper")
        items = modal.find_elements(By.CSS_SELECTOR, "li.unit-item")

        if not items:
            print("⚠️ 商品リストがありません")
            return False

        for item in items:
            try:
                bento_name = item.find_element(By.CLASS_NAME, "listOrder__title").text.strip()
                normalized_bento_name = normalize(bento_name)
                for order in order_info["orders"]:
                    if normalize(order["name"]) == normalized_bento_name:
                        input_el = item.find_element(By.CSS_SELECTOR, "input.input-quantity")
                        driver.execute_script("""
                            const input = arguments[0];
                            input.value = arguments[1];
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                        """, input_el, str(order["count"]))
                        time.sleep(1)
                        break
            except Exception as e:
                print(f"⚠️ 入力失敗: {e}")

        order_btn = modal.find_element(By.CLASS_NAME, "cart__submit")
        for _ in range(10):
            if not order_btn.get_attribute("disabled"):
                break
            time.sleep(1)

        driver.execute_script("arguments[0].click();", order_btn)
        time.sleep(2)

        try:
            error_popup = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "alert_wrapper"))
            )
            error_text = error_popup.text
            if "締め切られている" in error_text or "登録できません" in error_text:
                print("❌ 注文失敗:", error_text)
                driver.save_screenshot("order_failure_detected.png")
                comment_on_issue(order_info["number"], f"❌ 注文失敗：\n```\n{error_text}\n```\nご確認をお願いします。")
                mark_issue_as_failed(order_info["number"])
                return False
        except TimeoutException:
            print("✅ 注文エラーなし")

        WebDriverWait(driver, 10).until(EC.url_contains("/order/update"))
        print("✅ 注文完了")
        return True

    except TimeoutException:
        print("📸 注文途中でタイムアウト")
        return False

    finally:
        driver.quit()

if __name__ == "__main__":
    issues = fetch_pending_issues()
    for issue in issues:
        if perform_order(issue):
            mark_issue_as_ordered(issue["number"])
            comment_on_issue(issue["number"], f"✅ 注文完了：{issue['date']} の注文を受け付けました。")
