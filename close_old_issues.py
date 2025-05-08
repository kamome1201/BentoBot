import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

# 環境変数の読み込み
load_dotenv()

# トークンとリポジトリの設定
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("❌ GitHub Tokenが設定されていません。")
    exit(1)

REPO = "kamome1201/BentoBot"
ISSUES_URL = f"https://api.github.com/repos/{REPO}/issues"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# 昨日の日付
yesterday = datetime.utcnow() - timedelta(days=1)
yesterday_str = yesterday.strftime("%Y-%m-%d")

# Fetch all open issues with label "ordered"
def fetch_issues_to_close():
    issues = []
    page = 1
    while True:
        # GitHub API でページネーションを使用
        res = requests.get(f"{ISSUES_URL}?state=open&labels=ordered&per_page=100&page={page}", headers=HEADERS)
        if res.status_code != 200:
            print(f"❌ APIリクエストに失敗: {res.status_code} - {res.text}")
            break
        
        page_issues = res.json()
        if not page_issues:
            break
        
        for issue in page_issues:
            created_at = datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            
            # 注文日がissueの本文やラベルなどに含まれていると仮定
            # ここでは例としてissueのbodyに"注文日"という文字列があると仮定
            order_date = None
            if "注文日" in issue["body"]:
                order_date = re.search(r"注文日:\s*(\d{4}-\d{2}-\d{2})", issue["body"])
                if order_date:
                    order_date = order_date.group(1)

            if order_date and order_date == yesterday_str:
                issues.append(issue["number"])
        
        page += 1  # 次のページに進む
    
    return issues

# Close the issues
def close_issues(issue_numbers):
    for number in issue_numbers:
        url = f"{ISSUES_URL}/{number}"
        res = requests.patch(url, headers=HEADERS, json={"state": "closed"})
        if res.status_code == 200:
            print(f"✅ Issue #{number} をクローズしました")
        else:
            print(f"❌ Issue #{number} のクローズに失敗: {res.text}")
            # エラーが発生した場合、1秒待機して再試行する
            time.sleep(1)

if __name__ == "__main__":
    to_close = fetch_issues_to_close()
    if to_close:
        print(f"🔍 クローズ対象のIssueが{len(to_close)}件見つかりました。")
        close_issues(to_close)
    else:
        print("🔍 クローズ対象のIssueはありません")
