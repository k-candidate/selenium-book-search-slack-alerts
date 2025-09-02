from unittest.mock import Mock

import pytest

import main


def test_safe_send_keys_success():
    element = Mock()
    main.safe_send_keys(element, "test")
    element.send_keys.assert_called_once_with("test")


def test_safe_send_keys_stale_retries():
    element = Mock()
    # Raise StaleElementReferenceException on first two calls, succeed on third
    element.send_keys.side_effect = [
        main.StaleElementReferenceException,
        main.StaleElementReferenceException,
        None,
    ]
    main.safe_send_keys(element, "test", retries=3)
    assert element.send_keys.call_count == 3


def test_safe_send_keys_stale_raises():
    element = Mock()
    element.send_keys.side_effect = main.StaleElementReferenceException
    with pytest.raises(main.StaleElementReferenceException):
        main.safe_send_keys(element, "test", retries=2)
    assert element.send_keys.call_count == 2


def test_safe_clear_element_success():
    driver = Mock()
    element = Mock()
    main.safe_clear_element(driver, element)
    driver.execute_script.assert_called_once_with("arguments[0].value = '';", element)


def test_safe_clear_element_stale_retries():
    driver = Mock()
    element = Mock()
    driver.execute_script.side_effect = [
        main.StaleElementReferenceException,
        main.StaleElementReferenceException,
        None,
    ]
    main.safe_clear_element(driver, element, retries=3)
    assert driver.execute_script.call_count == 3


def test_safe_clear_element_stale_raises():
    driver = Mock()
    element = Mock()
    driver.execute_script.side_effect = main.StaleElementReferenceException
    with pytest.raises(main.StaleElementReferenceException):
        main.safe_clear_element(driver, element, retries=2)
    assert driver.execute_script.call_count == 2


def test_send_slack_message_success(monkeypatch):
    class DummyResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass

    def dummy_urlopen(req): return DummyResponse()

    monkeypatch.setattr("urllib.request.urlopen", dummy_urlopen)
    # Should print 'Slack message sent successfully.'
    main.send_slack_message("http://dummy-url.com", "test")


def test_send_slack_message_failure(monkeypatch, capsys):
    class DummyResponse:
        status = 400
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass

    def dummy_urlopen(req): return DummyResponse()

    monkeypatch.setattr("urllib.request.urlopen", dummy_urlopen)
    main.send_slack_message("http://dummy-url.com", "test")
    captured = capsys.readouterr()
    assert "Failed to send Slack message" in captured.out


def test_send_slack_message_exception(monkeypatch, capsys):
    def dummy_urlopen(req): raise Exception("forced error")

    monkeypatch.setattr("urllib.request.urlopen", dummy_urlopen)
    main.send_slack_message("http://dummy-url.com", "test")
    captured = capsys.readouterr()
    assert "Error sending message to Slack" in captured.out
