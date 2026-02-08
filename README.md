# selenium-book-search-slack-alerts
Automated script to search for books on a local bookstore's website using Selenium and send Slack alerts when books are found or errors occur.  
"Local bookstore" = Physically near me. It will not work with any bookstore website.

## Blog Posts
- [Python, Selenium, Slack, and GHA - Automating Book Availability Checks](https://k-candidate.github.io/2025/08/19/python-selenium-slack-automating-book-availability-checks.html)
- [pyproject.toml - Automating Book Availability Checks](https://k-candidate.github.io/2025/08/23/pyproject-toml.html)
- [Black, Isort, Mypy - Code Quality Checks - Automating Book Availability Checks](https://k-candidate.github.io/2025/08/24/black-isort-mypy-code-quality-checks.html)
- [pylock.toml - PEP 751 - Automating Book Availability Checks](https://k-candidate.github.io/2025/08/25/pylock-toml-pep-751.html)
- [Rustification of Python - uv, ruff, ty - Automating Book Availability Checks](https://k-candidate.github.io/2025/09/01/rustification-of-python-uv-ruff-ty.html)
- [Unit Tests - Pytest - Automating Book Availability Checks](https://k-candidate.github.io/2025/09/02/unit-tests-pytest.html)
- [Code Coverage - Automating Book Availability Checks](https://k-candidate.github.io/2025/09/16/code-coverage.html)
- [Tox - Automating Book Availability Checks](https://k-candidate.github.io/2025/12/06/tox.html)
- [Multi-threading - Automating Book Availability Checks](https://k-candidate.github.io/2025/12/08/multi-threading.html)
- [Further optimization - Automating Book Availability Checks](https://k-candidate.github.io/2025/12/09/chromium-installation-optimization.html)
- [Renovate bot - Automating Book Availability Checks](https://k-candidate.github.io/2025/12/10/renovatebot.html)
- [Shift Left and Reduce the Extraneous Cognitive Load with Git Pre-Commit Hooks - Automating Book Availability Checks](https://k-candidate.github.io/2026/01/11/git-pre-commit-hooks.html)
- [Integration Tests - Automating Book Availability Checks](https://k-candidate.github.io/2026/03/01/integration-tests.html)

## Usage

1. Install dependencies:
```
# clone repo
# cd repo
# uv tool install tox --with tox-uv
uv venv
source .venv/bin/activate
uv sync --locked --all-extras
```

2. Run the script with the required arguments:
```
python main.py --max-workers 4 --book-list "Sherlock Holmes; The snows of Kilimanjaro" --slack-webhook-url "https://hooks.slack.com/your/webhook" --website-url "https://my.local.bookstore"
```

## CLI Arguments

- `--max-workers`: Sunmber of threads to run in parallel
- `--book-list`: Semicolon-separated list of book titles to search
- `--slack-webhook-url`: Slack Incoming Webhook URL for sending notifications (required)
- `--website-url`: Target website URL to search books on (required)

## GitHub Actions Integration

A GitHub Actions workflow is included in `.github/workflows/check-books-periodically.yml` for continuous monitoring and notifications.

## Requirements

- Python
- Chromium
- ChromeDriver compatible with the Chromium version
