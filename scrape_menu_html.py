from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.binary_location = "/usr/bin/google-chrome"

driver = webdriver.Chrome(options=options)

try:
    driver.get("https://gluseller.com/menu/2025/4/24/105/show")
    time.sleep(10)

    # 全体HTMLの確認（オプション）
    print("==== ページ全体HTML ====")
    print(driver.page_source)
    print("==== ここまで ====")

    # 価格情報を含む要素の抽出
    print("==== 価格らしき要素 ====")
    price_elements = driver.find_elements(By.XPATH, "//*[contains(text(),'円')]")
    for el in price_elements:
        print(el.text)

    # <label> での抽出（必要なら）
    print("==== label要素の中に価格があるか ====")
    labels = driver.find_elements(By.TAG_NAME, "label")
    for label in labels:
        if "円" in label.text:
            print(label.text)

    # モーダル確認（もし必要なら）
    try:
        modal = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "modal-content"))
        )
        print("==== モーダル内HTML構造 ====")
        print(modal.get_attribute("innerHTML"))
        print("==== ここまで ====")
    except:
        print("モーダルが見つかりませんでした")

finally:
    driver.quit()
