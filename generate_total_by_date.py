
import requests
import json
import os
import re
from collections import defaultdict
from dotenv import load_dotenv
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

# Load environment variables
load_dotenv()

# GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "kamome1201/BentoBot"
ISSUES_URL = f"https://api.github.com/repos/{REPO}/issues"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# SMTP (Mail)
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
RECIPIENT = os.getenv("RECIPIENT")

# Fetch all issues labeled "bento-order"
def fetch_all_issues():
    issues = []
    page = 1
    while True:
        try:
            res = requests.get(f"{ISSUES_URL}?state=all&labels=bento-order&per_page=100&page={page}", headers=HEADERS, timeout=10)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ APIリクエストに失敗しました: {e}")
            break

        data = res.json()
        if not data:
            break
        issues.extend(data)
        page += 1
    return issues

# Parse issue body to extract date and orders
def parse_issue(issue):
    body = issue.get("body", "")
    date_match = re.search(r"【注文日】\s*(\d{4}-\d{2}-\d{2})", body)
    orders = re.findall(r"-\s*(.+?)\s*×\s*(\d+)", body)
    if not date_match:
        return None
    return {
        "date": date_match.group(1),
        "orders": [{"name": name, "count": int(qty)} for name, qty in orders]
    }

# Load price map from menu_today.json
menu_file = "static/menu_today.json"
if not os.path.exists(menu_file):
    print(f"❌ {menu_file} が見つかりません。ファイルが正しい場所にあるか確認してください。")
    exit(1)

with open(menu_file, "r", encoding="utf-8") as f:
    menu_data = json.load(f)
    price_map = {item["name"]: int(item["price"].replace("円", "")) for item in menu_data if item["name"] and item["price"]}

# Get today's date in the format YYYY-MM-DD
today = datetime.utcnow().strftime("%Y-%m-%d")

# Aggregate total price for today's orders
total_today = 0
for issue in fetch_all_issues():
    parsed = parse_issue(issue)
    if not parsed:
        continue
    if parsed["date"] == today:
        for order in parsed["orders"]:
            name = order["name"]
            count = order["count"]
            price = price_map.get(name, 0)
            total_today += price * count

# Save result
output_file = "static/total_today.json"
os.makedirs("static", exist_ok=True)
with open(output_file, "w", encoding="utf-8") as f:
    json.dump({"total_today": total_today}, f, ensure_ascii=False, indent=2)

print(f"✅ 当日の合計金額を {output_file} に保存しました。")

# Send summary email
def send_summary_email(total_amount):
    subject = f"[BentoBot] {datetime.today().strftime('%Y/%m/%d')}の注文合計"
    body = f"本日の合計金額は {total_amount} 円です。"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = RECIPIENT

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print("📧 注文合計の通知メールを送信しました。")
    except Exception as e:
        print(f"❌ メール送信に失敗しました: {e}")

# 実行
send_summary_email(total_today)
