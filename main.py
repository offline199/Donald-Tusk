import requests
from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")
        page.wait_for_load_state("domcontentloaded")
        print(page.inner_html("body"))
        browser.close()


if __name__ == "__main__":
    main()
