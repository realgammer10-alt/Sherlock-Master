from argparse import ArgumentTypeError

import pytest

from sherlock_project.notify import QueryNotifyPrint
from sherlock_project.result import QueryResult, QueryStatus
from sherlock_project.sherlock import timeout_check


@pytest.mark.parametrize(
    "status,http_status,expected",
    [
        (QueryStatus.CLAIMED, 200, "RESPONSIVE (HTTP 200)"),
        (QueryStatus.AVAILABLE, 404, "RESPONSIVE (HTTP 404)"),
        (QueryStatus.UNKNOWN, 503, "UNAVAILABLE (HTTP 503)"),
        (QueryStatus.UNKNOWN, None, "UNAVAILABLE (no HTTP response)"),
        (QueryStatus.ILLEGAL, None, "SKIPPED (invalid username)"),
    ],
)
def test_monitor_reports_live_endpoint_status(capsys, status, http_status, expected):
    notifier = QueryNotifyPrint(monitor=True, total_sites=1)
    notifier.start("alice")
    notifier.update(
        QueryResult(
            username="alice",
            site_name="Example",
            site_url_user="https://example.com/alice",
            status=status,
            query_time=0.025,
            http_status=http_status,
        )
    )

    output = capsys.readouterr().out
    assert "[1/1] Example:" in output
    assert expected in output
    assert "[25ms]" in output


def test_monitor_summarizes_endpoint_health(capsys):
    notifier = QueryNotifyPrint(monitor=True, total_sites=3)
    notifier.start("alice")
    for site, status, http_status in [
        ("Responsive", QueryStatus.CLAIMED, 200),
        ("Unavailable", QueryStatus.UNKNOWN, 503),
        ("Skipped", QueryStatus.ILLEGAL, None),
    ]:
        notifier.update(
            QueryResult(
                username="alice",
                site_name=site,
                site_url_user=f"https://example.com/{site}",
                status=status,
                http_status=http_status,
            )
        )

    notifier.finish()
    output = capsys.readouterr().out
    assert "Responsive (HTTP 1xx-4xx): 1" in output
    assert "Unavailable (HTTP 5xx/no response): 1" in output
    assert "Skipped (invalid username): 1" in output


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "-inf", "invalid"])
def test_timeout_check_rejects_non_positive_non_finite_or_invalid_values(value):
    with pytest.raises(ArgumentTypeError):
        timeout_check(value)


def test_timeout_check_accepts_positive_finite_values():
    assert timeout_check("0.5") == 0.5
