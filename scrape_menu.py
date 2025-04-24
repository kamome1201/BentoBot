from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import time

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

try:
    driver.get("https://gluseller.com/menu/2025/4/24/105/show")
    time.sleep(5)  # ページ読み込み待ち

    # メニュー項目をざっくり取得（HTML構造に応じて変更が必要）
    items = driver.find_elements(By.CSS_SELECTOR, "div")  # 仮: itemごとのdiv

    data = []
    for el in items:
        text = el.text.strip()
        if "弁当" in text and "円" in text:
            lines = text.split("\n")
            for line in lines:
                if "円" in line:
                    menu, price = line.rsplit(" ", 1)
                    data.append({"menu": menu.strip(), "price": price.strip()})

    # 画像URL（最初のimgなど）
    img = driver.find_element(By.TAG_NAME, "img")
    img_url = img.get_attribute("src")

    df = pd.DataFrame(data)
    df["image"] = img_url
    df.to_csv("menu_list.csv", index=False)
    print(df)

finally:
    driver.quit()
