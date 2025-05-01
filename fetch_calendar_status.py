from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from collections import defaultdict
import time
import json

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)
url = "https://gluseller.com/#top_order"

try:
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "showOrder")))
    time.sleep(3)

    cells = driver.find_elements(By.CSS_SELECTOR, "td[class*='calendar-day']")
    status_map = defaultdict(lambda: "normal")

    for cell in cells:
        try:
            date_span = cell.find_element(By.CLASS_NAME, "calendar-date-number")
            day = int(date_span.text.strip())
            today = datetime.now()
            date = datetime(today.year, today.month, day).strftime("%Y-%m-%d")

            class_attr = cell.get_attribute("class")
            text = cell.text

            if "calendar-holiday" in class_attr or "休業日" in text:
                status_map[date] = "holiday"
            elif "calendar-premium" in class_attr:
                status_map[date] = "premium"
            elif "calendar-special" in class_attr:
                status_map[date] = "special"
        except:
            continue

    with open("docs/calendar_status.json", "w", encoding="utf-8") as f:
        json.dump(status_map, f, ensure_ascii=False, indent=2)

    print("✅ calendar_status.json を生成しました")
finally:
    driver.quit()
