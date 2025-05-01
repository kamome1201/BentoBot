import requests
import json
import os
import re
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "kamome1201/BentoBot"
ISSUES_URL = f"https://api.github.com/repos/{REPO}/issues"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Fetch all issues labeled "bento-order"
def fetch_all_issues():
    issues = []
    page = 1
    while True:
        res = requests.get(f"{ISSUES_URL}?state=all&labels=bento-order&per_page=100&page={page}", headers=HEADERS)
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
with open("docs/menu_today.json", "r", encoding="utf-8") as f:
    menu_data = json.load(f)
    price_map = {item["name"]: int(item["price"].replace("円", "")) for item in menu_data if item["name"] and item["price"]}

# Aggregate total price by date
total_by_date = defaultdict(int)
for issue in fetch_all_issues():
    parsed = parse_issue(issue)
    if not parsed:
        continue
    for order in parsed["orders"]:
        name = order["name"]
        count = order["count"]
        price = price_map.get(name, 0)
        total_by_date[parsed["date"]] += price * count

# Save result
with open("docs/total_by_date.json", "w", encoding="utf-8") as f:
    json.dump(total_by_date, f, ensure_ascii=False, indent=2)

print("✅ total_by_date.json を生成しました")
