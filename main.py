from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main():
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=300,300")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://www.olx.pl/motoryzacja/q-samochody-osobowe/")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        print(driver.find_element(By.TAG_NAME, "body").get_attribute("innerHTML").strip())

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
