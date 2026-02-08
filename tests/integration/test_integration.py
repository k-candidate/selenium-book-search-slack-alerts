from typing import Any, Dict, List, Tuple

import argparse
import time

import main


def test_main_collects_and_sorts_results(monkeypatch: Any, capsys: Any) -> None:
    # Prevent real network calls to Slack
    monkeypatch.setattr(main, "send_slack_message", lambda *a, **k: None)

    # Provide predictable CLI args
    def fake_parse_args() -> argparse.Namespace:
        return argparse.Namespace(
            book_list="Zeta; Alpha; Beta",
            slack_webhook_url="http://dummy",
            website_url="http://site",
            max_workers=2,
        )

    monkeypatch.setattr(main, "parse_args", fake_parse_args)

    # Replace the real selenium-driven check with a lightweight fake
    calls: List[Tuple[int, str]] = []

    def fake_check_single_book(
        book: str, index: int, slack_webhook_url: str, website_url: str
    ) -> Dict[str, Any]:
        # Stagger completion times to simulate out-of-order finishes
        if book.strip() == "Zeta":
            time.sleep(0.02)
        elif book.strip() == "Alpha":
            time.sleep(0.03)
        else:
            time.sleep(0.0)
        calls.append((index, book.strip()))
        return {"index": index, "book": book.strip(), "status": "available"}

    monkeypatch.setattr(main, "check_single_book", fake_check_single_book)

    # Run the program (uses ThreadPoolExecutor internally)
    main.main()

    captured = capsys.readouterr()

    assert "Checking 3 books with 2 concurrent browsers..." in captured.out
    assert "All searches completed!" in captured.out

    # Results should be sorted by index in the final output
    assert "Book #1 'Zeta': available" in captured.out
    assert "Book #2 'Alpha': available" in captured.out
    assert "Book #3 'Beta': available" in captured.out

    # Ensure the fake check was invoked for each book
    assert len(calls) == 3
