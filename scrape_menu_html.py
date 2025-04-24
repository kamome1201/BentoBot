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
    time.sleep(5)

    print("==== ページ全体HTML ====")
    print(driver.page_source)
    print("==== ここまで ====")

    modal = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal-content"))
    )
    print("==== モーダル内HTML構造 ====")
    print(modal.get_attribute("innerHTML"))
    print("==== ここまで ====")

finally:
    driver.quit()
