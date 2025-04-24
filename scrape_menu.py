from selenium import webdriver
from selenium.webdriver.common.by import By
import time

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.binary_location = "/usr/bin/google-chrome"

driver = webdriver.Chrome(options=options)

try:
    # 対象ページにアクセス
    driver.get("https://gluseller.com/menu/2025/4/24/105/show")
    time.sleep(5)  # ページの読み込み待ち

    # モーダル内のHTMLを取得して出力
    modal = driver.find_element(By.CLASS_NAME, "modal-content")
    print("==== モーダル内HTML構造 ====")
    print(modal.get_attribute("innerHTML"))
    print("==== ここまで ====")

finally:
    driver.quit()
