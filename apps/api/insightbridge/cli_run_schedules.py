"""Run due scheduled reports once. Usage: from repo root, with API venv active:
  cd apps/api && python -m insightbridge.cli_run_schedules
"""
from insightbridge.delivery.runner import run_due_scheduled_reports


def main() -> None:
    print(run_due_scheduled_reports())


if __name__ == "__main__":
    main()
