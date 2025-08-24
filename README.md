# selenium-book-search-slack-alerts
Automated script to search for books on a local bookstore's website using Selenium and send Slack alerts when books are found or errors occur.  
"Local bookstore" = Physically near me. It will not work with any bookstore website.

## Blog Posts
- [Python, Selenium, Slack, and GHA - Automating Book Availability Checks](https://k-candidate.github.io/2025/08/19/python-selenium-slack-automating-book-availability-checks.html)

## Usage

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Run the script with the required arguments:
```
python main.py --book-list "Sherlock Holmes; The snows of Kilimanjaro" --slack-webhook-url "https://hooks.slack.com/your/webhook" --website-url "https://my.local.bookstore"
```

## CLI Arguments

- `--book-list`: Semicolon-separated list of book titles to search
- `--slack-webhook-url`: Slack Incoming Webhook URL for sending notifications (required)
- `--website-url`: Target website URL to search books on (required)

## GitHub Actions Integration

A GitHub Actions workflow is included in `.github/workflows/check-books-periodically.yml` for continuous monitoring and notifications.

## Requirements

- Python
- Chromium
- ChromeDriver compatible with the Chromium version
