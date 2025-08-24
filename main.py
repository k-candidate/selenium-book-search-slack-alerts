import argparse
import json
import time
import urllib.request

from selenium import webdriver
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check book availability and notify Slack"
    )
    parser.add_argument(
        "--book-list",
        type=str,
        default="Robinson Crusoe; Amin Maalouf; Dr. Seuss",
        help='Semicolon-separated list of books to check, e.g. "Book1; Book Number2; Book3"',
    )
    parser.add_argument(
        "--slack-webhook-url",
        required=True,
        help="Slack webhook URL for sending notifications",
    )
    parser.add_argument(
        "--website-url", required=True, help="Target website URL to search in"
    )
    return parser.parse_args()


def safe_send_keys(element: WebElement, keys: str, retries: int = 3) -> None:
    """Send keys to element retrying if StaleElementReferenceException occurs."""
    for i in range(retries):
        try:
            element.send_keys(keys)
            return
        except StaleElementReferenceException:
            if i == retries - 1:
                raise
            time.sleep(0.5)  # small delay before retry


def safe_clear_element(
    driver: WebDriver, element: WebElement, retries: int = 3
) -> None:
    """
    Clear input element value using JS to avoid interact issues, with retries.
    I tried search_bar.clear() but it did not work.
    """
    for i in range(retries):
        try:
            driver.execute_script("arguments[0].value = '';", element)
            return
        except StaleElementReferenceException:
            if i == retries - 1:
                raise
            time.sleep(0.5)


def send_slack_message(webhook_url: str, text: str) -> None:
    data = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("Slack message sent successfully.")
            else:
                print(f"Failed to send Slack message: HTTP {response.status}.")
    except Exception as e:
        print(f"Error sending message to Slack: {str(e)}.")


def main() -> None:
    args = parse_args()

    book_list = [book.strip() for book in args.book_list.split(";")]
    slack_webhook_url = args.slack_webhook_url
    website_url = args.website_url

    chromedriver_path = "/snap/bin/chromium.chromedriver"
    service = Service(executable_path=chromedriver_path)

    options = Options()
    # Uncomment to keep browser open for local debugging
    # options.add_experimental_option("detach", True)
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=service, options=options)
    driver.get(website_url)

    wait = WebDriverWait(driver, 60)

    for index, book in enumerate(book_list, start=1):
        try:
            print(f"Book #{index} - Processing...")

            # Re-locate search bar before each search to avoid selenium.common.exceptions.StaleElementReferenceException
            search_bar = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "div.panel-busqueda input#buscar")
                )
            )
            safe_clear_element(driver, search_bar)
            safe_send_keys(search_bar, book)
            safe_send_keys(search_bar, Keys.RETURN)

            # Wait for either product results or no result message
            wait.until(
                lambda d: d.find_elements(By.CSS_SELECTOR, "div.producto")
                or d.find_elements(
                    By.CSS_SELECTOR, "span.sin-resultados-busqueda-avanzada"
                )
            )

            products = driver.find_elements(By.CSS_SELECTOR, "div.producto")
            if products:
                msg = f"#{index} '{book}' - Book is available!"
                anon_msg = f"Book #{index} - Book is available!"
                print(anon_msg)
                send_slack_message(slack_webhook_url, msg)
            else:
                no_results = driver.find_elements(
                    By.CSS_SELECTOR, "span.sin-resultados-busqueda-avanzada"
                )
                if no_results:
                    print(f"Book #{index} - No results found.")
                else:
                    msg = f"#{index} '{book}' - Search results unavailable or page structure changed."
                    anon_msg = f"Book #{index} - Search results unavailable or page structure changed."
                    print(anon_msg)
                    send_slack_message(slack_webhook_url, msg)

        except TimeoutException:
            error_msg = f"#{index} '{book}' - Timed out waiting for search results to load."
            anon_error_msg = f"Book #{index} - Timed out waiting for search results to load."
            print(anon_error_msg)
            send_slack_message(slack_webhook_url, error_msg)
        except StaleElementReferenceException:
            error_msg = f"#{index} '{book}' - Stale element reference exception on input or results."
            anon_error_msg = f"Book #{index} - Stale element reference exception on input or results."
            print(anon_error_msg)
            send_slack_message(slack_webhook_url, error_msg)

        # Delay between searches to reduce load on server, and avoid blocks or rate-limiting
        time.sleep(1)

    # Close the browser session
    driver.quit()


if __name__ == "__main__":
    main()
