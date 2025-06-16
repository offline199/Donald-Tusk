from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main():
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    # chrome_options.add_argument("--no-sandbox") # Often needed in CI/CD environments
    # chrome_options.add_argument("--disable-dev-shm-usage") # Often needed in CI/CD environments

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Navigate to the URL
        driver.get("https://example.com")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Print the inner HTML of the body
        print(driver.find_element(By.TAG_NAME, "body").get_attribute("innerHTML").strip())

    finally:
        # Close the browser
        driver.quit()


if __name__ == "__main__":
    main()
