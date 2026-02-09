from typing import Any, Generator

from unittest.mock import Mock, patch, MagicMock

import argparse

import pytest

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

import main


@pytest.fixture
def mock_args() -> Generator[MagicMock, None, None]:
    with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
        yield mock_parse_args

def test_parse_args_default(mock_args: MagicMock) -> None:
    mock_args.return_value = argparse.Namespace(
        book_list="Robinson Crusoe; Amin Maalouf; Dr. Seuss",
        slack_webhook_url='http://dummy',
        website_url='http://example.com',
        max_workers=2
    )
    args = main.parse_args()
    assert args.book_list == "Robinson Crusoe; Amin Maalouf; Dr. Seuss"
    assert args.slack_webhook_url == 'http://dummy'
    assert args.website_url == 'http://example.com'

def test_parse_args_custom_book_list(mock_args: MagicMock) -> None:
    mock_args.return_value = argparse.Namespace(
        book_list="Book A; Book B",
        slack_webhook_url='http://dummy',
        website_url='http://example.com',
        max_workers=3
    )
    args = main.parse_args()
    assert args.book_list == "Book A; Book B"
    assert args.slack_webhook_url == 'http://dummy'
    assert args.website_url == 'http://example.com'
    assert args.max_workers == 3


def test_safe_send_keys_success() -> None:
    element = Mock()
    main.safe_send_keys(element, "test")
    element.send_keys.assert_called_once_with("test")


def test_safe_send_keys_stale_retries() -> None:
    element = Mock()
    # Raise StaleElementReferenceException on first two calls, succeed on third
    element.send_keys.side_effect = [
        StaleElementReferenceException,
        StaleElementReferenceException,
        None,
    ]
    main.safe_send_keys(element, "test", retries=3)
    assert element.send_keys.call_count == 3


def test_safe_send_keys_stale_raises() -> None:
    element = Mock()
    element.send_keys.side_effect = StaleElementReferenceException
    with pytest.raises(StaleElementReferenceException):
        main.safe_send_keys(element, "test", retries=2)
    assert element.send_keys.call_count == 2


def test_safe_clear_element_success() -> None:
    driver = Mock()
    element = Mock()
    main.safe_clear_element(driver, element)
    driver.execute_script.assert_called_once_with("arguments[0].value = '';", element)


def test_safe_clear_element_stale_retries() -> None:
    driver = Mock()
    element = Mock()
    driver.execute_script.side_effect = [
        StaleElementReferenceException,
        StaleElementReferenceException,
        None,
    ]
    main.safe_clear_element(driver, element, retries=3)
    assert driver.execute_script.call_count == 3


def test_safe_clear_element_stale_raises() -> None:
    driver = Mock()
    element = Mock()
    driver.execute_script.side_effect = StaleElementReferenceException
    with pytest.raises(StaleElementReferenceException):
        main.safe_clear_element(driver, element, retries=2)
    assert driver.execute_script.call_count == 2


def test_send_slack_message_success(monkeypatch: Any) -> None:
    class DummyResponse:
        status = 200

        def __enter__(self) -> "DummyResponse":
            return self

        def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

    def dummy_urlopen(req: Any) -> DummyResponse:
        return DummyResponse()

    monkeypatch.setattr("urllib.request.urlopen", dummy_urlopen)
    # Should print 'Slack message sent successfully.'
    main.send_slack_message("http://dummy-url.com", "test")


def test_send_slack_message_failure(monkeypatch: Any, capsys: Any) -> None:
    class DummyResponse:
        status = 400

        def __enter__(self) -> "DummyResponse":
            return self

        def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

    def dummy_urlopen(req: Any) -> DummyResponse:
        return DummyResponse()

    monkeypatch.setattr("urllib.request.urlopen", dummy_urlopen)
    main.send_slack_message("http://dummy-url.com", "test")
    captured = capsys.readouterr()
    assert "Failed to send Slack message" in captured.out


def test_send_slack_message_exception(monkeypatch: Any, capsys: Any) -> None:
    def dummy_urlopen(req: Any) -> None:
        raise Exception("forced error")

    monkeypatch.setattr("urllib.request.urlopen", dummy_urlopen)
    main.send_slack_message("http://dummy-url.com", "test")
    captured = capsys.readouterr()
    assert "Error sending message to Slack" in captured.out

@patch("main.webdriver.Chrome")
@patch("main.WebDriverWait")
def test_check_single_book_available(
    mock_wait: MagicMock, mock_driver: MagicMock, monkeypatch: Any
) -> None:
    # Mock driver setup
    mock_driver_instance = MagicMock()
    mock_driver.return_value.__enter__.return_value = mock_driver_instance
    mock_driver_instance.get.return_value = None

    # Mock search elements
    mock_search_bar = MagicMock()
    mock_driver_instance.find_element.return_value = mock_search_bar

    # Mock wait conditions
    mock_wait_instance = MagicMock()
    mock_wait.return_value.__enter__.return_value = mock_wait_instance
    mock_wait_instance.until.return_value = mock_search_bar

    # Mock products found
    mock_driver_instance.find_elements.return_value = [MagicMock()]

    monkeypatch.setattr("main.send_slack_message", lambda *args: None)

    result = main.check_single_book("Test Book", 1, "http://slack", "http://site")

    assert result == {"index": 1, "book": "Test Book", "status": "available"}



def setup_common(monkeypatch: Any) -> None:
    # Prevent any real Slack calls
    monkeypatch.setattr("main.send_slack_message", lambda *args, **kwargs: None)


@patch("main.webdriver.Chrome")
@patch("main.WebDriverWait")
def test_check_single_book_not_found(mock_wait: MagicMock, mock_chrome: MagicMock, monkeypatch: Any) -> None:
    setup_common(monkeypatch)

    driver = MagicMock()
    mock_chrome.return_value = driver

    # Wait returns a clickable element
    mock_wait.return_value.until.return_value = MagicMock()

    # First call to find_elements for products -> empty
    # Second call for no_results -> list with a marker
    def find_elements(css_selector: str) -> list[Any]:
        if "div.producto" in css_selector:
            return []
        return [MagicMock()]

    # args[1] is the selector string passed to find_elements
    driver.find_elements.side_effect = lambda *args, **kwargs: find_elements(args[1])

    res = main.check_single_book("Book X", 2, "http://slack", "http://site")
    assert res["status"] == "not_found"


@patch("main.webdriver.Chrome")
@patch("main.WebDriverWait")
def test_check_single_book_structure_changed(mock_wait: MagicMock, mock_chrome: MagicMock, monkeypatch: Any) -> None:
    setup_common(monkeypatch)

    driver = MagicMock()
    mock_chrome.return_value = driver

    mock_wait.return_value.until.return_value = MagicMock()

    # No products and no no-results marker
    driver.find_elements.return_value = []

    res = main.check_single_book("Book Y", 3, "http://slack", "http://site")
    assert res["status"] == "error"


@patch("main.webdriver.Chrome")
@patch("main.WebDriverWait")
def test_check_single_book_timeout(mock_wait: MagicMock, mock_chrome: MagicMock, monkeypatch: Any) -> None:
    setup_common(monkeypatch)

    # Make wait.until raise TimeoutException
    mock_wait.return_value.until.side_effect = TimeoutException

    # Chrome will be created but won't get to results
    mock_chrome.return_value = MagicMock()

    res = main.check_single_book("Book Z", 4, "http://slack", "http://site")
    assert res["status"] == "timeout"


def test_check_single_book_stale_on_chrome(monkeypatch: Any) -> None:
    setup_common(monkeypatch)

    # Make webdriver.Chrome raise StaleElementReferenceException
    monkeypatch.setattr("main.webdriver.Chrome", lambda *args, **kwargs: (_ for _ in ()).throw(StaleElementReferenceException()))

    res = main.check_single_book("Book S", 5, "http://slack", "http://site")
    assert res["status"] == "stale"


def test_main_runs_with_patched_check(monkeypatch: Any, capsys: Any) -> None:
    # Patch parse_args to control inputs
    monkeypatch.setattr(
        "argparse.ArgumentParser.parse_args",
        lambda self=None: argparse.Namespace(
            book_list="A;B",
            slack_webhook_url="http://slack",
            website_url="http://site",
            max_workers=1,
        ),
    )

    # Patch check_single_book to return predictable results
    monkeypatch.setattr(
        "main.check_single_book",
        lambda book, index, slack, site: {"index": index, "book": book, "status": "available"},
    )

    main.main()
    captured = capsys.readouterr()
    assert "All searches completed!" in captured.out
