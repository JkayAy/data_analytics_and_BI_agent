from __future__ import annotations

import csv
import io

from insightbridge.db import list_query_runs_for_org


def query_runs_to_csv(org_id: str, *, limit: int = 5000) -> str:
    rows = list_query_runs_for_org(org_id, limit=limit)
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=[
            "id",
            "question_text",
            "status",
            "row_count",
            "duration_ms",
            "error_message",
            "created_at",
            "sql_text",
        ],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in writer.fieldnames})
    return buf.getvalue()
