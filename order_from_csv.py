import csv
import requests
import os
from dotenv import load_dotenv

# .envからトークンを読み込む（必要であれば）
load_dotenv()
API_URL_TEMPLATE = "https://gluseller.com/api/order/{year}/{month}/general"
HEADERS = {
    "Content-Type": "application/json"
}

def load_orders(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        orders_by_date = {}
        for row in reader:
            date = row['date']
            item = row['name']
            count = int(row['count'])
            orders_by_date.setdefault(date, []).append({
                "name": item,
                "count": count
            })
        return orders_by_date

def send_orders(date, items):
    year, month, _ = date.split('-')
    url = API_URL_TEMPLATE.format(year=year, month=int(month))
    payload = {
        "date": date,
        "orders": items
    }

    response = requests.post(url, json=payload, headers=HEADERS)
    print(f"[{date}] Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ 注文成功:", response.json())
    else:
        print("❌ 注文失敗:", response.text)

if __name__ == "__main__":
    orders_by_date = load_orders("orders.csv")
    for date, items in orders_by_date.items():
        send_orders(date, items)
