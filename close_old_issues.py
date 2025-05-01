import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "kamome1201/BentoBot"
ISSUES_URL = f"https://api.github.com/repos/{REPO}/issues"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# 今日 - 1日
cutoff_date = datetime.utcnow() - timedelta(days=1)

# Fetch all open issues with label "ordered"
def fetch_issues_to_close():
    res = requests.get(f"{ISSUES_URL}?state=open&labels=ordered&per_page=100", headers=HEADERS)
    issues = res.json()
    to_close = []
    for issue in issues:
        created_at = datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        if created_at < cutoff_date:
            to_close.append(issue["number"])
    return to_close

# Close the issues
def close_issues(issue_numbers):
    for number in issue_numbers:
        url = f"{ISSUES_URL}/{number}"
        res = requests.patch(url, headers=HEADERS, json={"state": "closed"})
        if res.status_code == 200:
            print(f"✅ Issue #{number} をクローズしました")
        else:
            print(f"❌ Issue #{number} のクローズに失敗: {res.text}")

if __name__ == "__main__":
    to_close = fetch_issues_to_close()
    if to_close:
        close_issues(to_close)
    else:
        print("🔍 クローズ対象のIssueはありません")
