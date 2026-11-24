"""Generate reports/data_quality/data_quality_report.csv."""
from quality_checks import connect, run_checks, summarize, save_report

def main():
    con = connect()
    try:
        results = run_checks(con)
        failures = summarize(results)
        print("CSV report:", save_report(results))
        return 1 if failures else 0
    finally:
        con.close()

if __name__ == "__main__":
    raise SystemExit(main())
