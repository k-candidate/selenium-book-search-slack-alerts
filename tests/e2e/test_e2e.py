import os
from typing import Any
from types import SimpleNamespace

import main


def test_e2e_search_two_books_real_browser(monkeypatch: Any, capsys: Any) -> None:
    # Prevent real Slack network calls while using a real browser
    monkeypatch.setattr(main, "send_slack_message", lambda *a, **k: None)

    # Provide CLI args using the WEBSITE_URL secret and slack webhook
    def real_parse_args() -> SimpleNamespace:
        return SimpleNamespace(
            book_list="1984; dfvtvrbg",
            slack_webhook_url=os.environ.get("SLACK_WEBHOOK_URL", "http://dummy"),
            website_url=os.environ.get("WEBSITE_URL", "http://dummy-site"),
            max_workers=2,
        )

    monkeypatch.setattr(main, "parse_args", real_parse_args)

    # Run the program using the real Selenium-driven browser installed in the runner
    main.main()

    captured = capsys.readouterr()
    print(f"\n=== TEST OUTPUT ===\n{captured.out}")

    # Verify expected statuses
    assert "Book #1 '1984': available" in captured.out
    assert "Book #2 'dfvtvrbg': not_found" in captured.out
