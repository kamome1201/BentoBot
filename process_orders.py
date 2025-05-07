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
GITHUB_TOKEN = os.getenv("GH_TOKEN")
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
    orders = re.findall(r"-\s*(.+?)\s*\u00d7\s*(\d+)", body)
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
        print("✅ 注文ページへ遷移しました")

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

        time.sleep(1)
        if not target_cell:
            print(f"❌ {date_str} に対応する注文可能な日付セルが見つかりません。")
            return False

        driver.execute_script("arguments[0].click();", target_cell)
        print(f"✅ {day_number}日 をクリックしました")

        for i, y in enumerate([600, 1200, 1800]):
            driver.execute_script(f"window.scrollTo(0, {y});")
            time.sleep(1)
            driver.save_screenshot(f"debug_after_click_scroll_{i}.png")
        print("📸 カレンダークリック後の状態をスクロールして撮影しました")

        WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CLASS_NAME, "modaal-content-container")))
        print("✅ モーダルが表示されました")
        time.sleep(2)
        modal = driver.find_element(By.CLASS_NAME, "modaal-wrapper")
        items = modal.find_elements(By.CSS_SELECTOR, "li.unit-item")

        if not items:
            print("⚠️ 商品リストがありません")
            driver.save_screenshot("debug_no_items_modal.png")
            return False

        for item in items:
            try:
                bento_name = item.find_element(By.CLASS_NAME, "listOrder__title").text.strip()
                normalized_bento_name = normalize(bento_name)
                matched = False

                for order in order_info["orders"]:
                    if normalize(order["name"]) == normalized_bento_name:
                        input_el = item.find_element(By.CSS_SELECTOR, "input.input-quantity")
                        driver.execute_script("""
                            const input = arguments[0];
                            input.value = arguments[1];
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                        """, input_el, str(order["count"]))
                        print(f"✅ {normalized_bento_name} ← {order['count']}個（入力成功）")
                        matched = True
                        time.sleep(2)
                        break

                if not matched:
                    print(f"❔ 商品名不一致: 注文='{order['name']}', 表示='{bento_name}'")
            except Exception as e:
                print(f"⚠️ 入力失敗: {e}")

        order_btn = modal.find_element(By.CLASS_NAME, "cart__submit")
        for _ in range(10):
            if not order_btn.get_attribute("disabled"):
                break
            time.sleep(1)
        else:
            print("❌ 注文ボタンが有効になりません")
            driver.save_screenshot("debug_input.png")
            return False

        driver.save_screenshot("debug_input.png")
        driver.execute_script("arguments[0].click();", order_btn)
        print("✅ 注文ボタンをクリックしました")
        time.sleep(2)

        WebDriverWait(driver, 10).until(EC.url_contains("/order/update"))
        print("✅ 注文完了ページへ遷移しました")
        driver.save_screenshot("final.png")
        time.sleep(2)

        return True

    except TimeoutException:
        driver.save_screenshot("debug_input.png")
        print("📸 debug_input.png を保存しました（タイムアウト）")
        return False

    finally:
        driver.quit()

def comment_on_issue(issue_number, message):
    url = f"{ISSUES_URL}/{issue_number}/comments"
    res = requests.post(url, headers=HEADERS, json={"body": message})
    if res.status_code == 201:
        print(f"📝 Issue #{issue_number} にコメントしました。")
    else:
        print(f"❌ コメント失敗: {res.text}")

if __name__ == "__main__":
    issues = fetch_pending_issues()
    for issue in issues:
        if perform_order(issue):
            mark_issue_as_ordered(issue["number"])
#            comment_on_issue(issue["number"], f"✅ {issue['date']} の注文を受け付けました。")
#        else:
#            comment_on_issue(issue["number"], f"❌ {issue['date']} の注文に失敗しました。再確認をお願いします。")
