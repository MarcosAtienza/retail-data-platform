"""Print the data-quality results and exit nonzero on ERROR failures."""
from quality_checks import connect, run_checks, summarize

def main():
    con = connect()
    try:
        return 1 if summarize(run_checks(con)) else 0
    finally:
        con.close()

if __name__ == "__main__":
    raise SystemExit(main())
