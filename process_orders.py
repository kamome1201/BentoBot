import requests
import json
import os
import re
from dotenv import load_dotenv
from datetime import datetime

# Load GitHub token and repo info
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "kamome1201/BentoBot"
ISSUES_URL = f"https://api.github.com/repos/{REPO}/issues"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Helper to parse issue body
def parse_issue(issue):
    body = issue.get("body", "")
    date_match = re.search(r"【注文日】\s*(\d{4}-\d{2}-\d{2})", body)
    orders = re.findall(r"-\s*(.+?)\s*×\s*(\d+)", body)
    if not date_match:
        return None
    return {
        "number": issue["number"],
        "title": issue["title"],
        "date": date_match.group(1),
        "orders": [{"name": name, "count": int(qty)} for name, qty in orders]
    }

# Fetch all open issues labeled "bento-order" but not yet "ordered"
def fetch_pending_issues():
    res = requests.get(f"{ISSUES_URL}?state=open&labels=bento-order", headers=HEADERS)
    issues = res.json()
    pending = []
    for issue in issues:
        if not any(label["name"] == "ordered" for label in issue.get("labels", [])):
            parsed = parse_issue(issue)
            if parsed:
                pending.append(parsed)
    return pending

# Placeholder: perform order on gluseller (should be implemented with Selenium)
def perform_order(order_info):
    print(f"[MOCK] 注文実行: {order_info['date']} の注文を gluseller に送信中...")
    for item in order_info['orders']:
        print(f" - {item['name']} x {item['count']}")
    return True  # Simulate success

# Mark issue as ordered
def mark_issue_as_ordered(issue_number):
    url = f"{ISSUES_URL}/{issue_number}"
    res = requests.patch(url, headers=HEADERS, json={"labels": ["bento-order", "ordered"]})
    if res.status_code == 200:
        print(f"✅ Issue #{issue_number} に 'ordered' ラベルを追加しました。")
    else:
        print(f"❌ Issue #{issue_number} 更新失敗: {res.text}")

if __name__ == "__main__":
    issues = fetch_pending_issues()
    for issue in issues:
        success = perform_order(issue)
        if success:
            mark_issue_as_ordered(issue["number"])
