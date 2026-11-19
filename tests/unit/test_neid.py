import pytest

from flinch import neid
from flinch.timeutil import jd_to_datetime, year_start_jd

ANSWER = (
    "obsjd,exptime,ccfrvmod,dvrms\n"
    "2460445.189645670,55.0,-0.6397,0.0003\n"
    "2460445.190600500,55.0,-0.6421,0.0003\n"
)


def test_parse_csv_reads_a_table():
    table = neid.parse_csv(ANSWER, "obsjd")
    assert len(table) == 2
    assert table["ccfrvmod"].iloc[0] == pytest.approx(-0.6397)


def test_parse_csv_rejects_an_error_message():
    with pytest.raises(RuntimeError, match="unexpected answer"):
        neid.parse_csv("Failed to execute select statement: ORA-01843: not a valid month", "obsjd")


def test_download_queries_one_year_at_a_time(tmp_path, monkeypatch):
    queries = []

    def fake_fetch(url, params=None, **kwargs):
        queries.append(params["query"])
        # 2460310.5 is 2024-01-01: only the query that starts there (year 2024) returns rows.
        return ANSWER if ">= 2460310.5" in params["query"] else "obsjd,exptime,ccfrvmod,dvrms\n"

    monkeypatch.setattr(neid, "fetch_text", fake_fetch)
    monkeypatch.setattr(neid, "COLUMNS", ("obsjd", "exptime", "ccfrvmod", "dvrms"))
    path = neid.download_solar_table(tmp_path / "table.csv.gz", last_year=2024)
    assert len(queries) == 5  # 2020 to 2024
    assert all("from neidsolarl2" in q for q in queries)
    table = neid.read_solar_table(path)
    assert len(table) == 2  # only the 2024 query returned rows
    assert table["rv_ms"].iloc[0] == pytest.approx(-639.7)
    assert table["rv_err_ms"].iloc[0] == pytest.approx(0.3)


def test_year_boundaries():
    assert year_start_jd(2024) == pytest.approx(2460310.5)
    assert str(jd_to_datetime(2460445.189645670))[:16] == "2024-05-14 16:33"
