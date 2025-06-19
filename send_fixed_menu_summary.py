import os
import json
import smtplib
from email.mime.text import MIMEText
from collections import defaultdict
from datetime import datetime

ORDERS_FILE = "static/orders.json"
MENU_FILE = "static/menu_today.json"
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_ADDR = os.getenv("FROM_ADDR")
TO_ADDR = os.getenv("TO_ADDR")

def get_himawari_menu_names():
    with open(MENU_FILE, encoding="utf-8") as f:
        menu = json.load(f)
    return set(item["name"] for item in menu if item.get("type") == "fixed_menu")

def summarize_himawari_orders(orders, himawari_names):
    date_to_orders = defaultdict(lambda: defaultdict(int))
    for order in orders:
        date = order.get("order_date")
        for o in order.get("orders", []):
            if o["name"] in himawari_names:
                date_to_orders[date][o["name"]] += int(o["count"])
    return date_to_orders

def send_himawari_summary(date, orders):
    body_lines = [f"【{date}のひまわり注文まとめ】"]
    for name, count in orders.items():
        body_lines.append(f"- {name} × {count}")
    body = "\n".join(body_lines)

    msg = MIMEText(body)
    msg['Subject'] = f"[BentoBot] Himawari order summary for {date}"
    msg['From'] = FROM_ADDR
    msg['To'] = TO_ADDR

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

def main():
    with open(ORDERS_FILE, encoding="utf-8") as f:
        orders = json.load(f)
    himawari_names = get_himawari_menu_names()
    summaries = summarize_himawari_orders(orders, himawari_names)
    today = datetime.now().strftime("%Y-%m-%d")
    if today in summaries and summaries[today]:
        send_himawari_summary(today, summaries[today])
        print(f"Sent Himawari summary for {today}!")
    else:
        print("No Himawari orders to notify today.")

if __name__ == "__main__":
    main()
