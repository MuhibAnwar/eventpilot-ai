"""Write sample_participants.xlsx with synthetic demo rows."""

from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.sample_data import SAMPLE_ROWS  # noqa: E402

OUT = ROOT / "sample_participants.xlsx"


def main() -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Participants"
    ws.append(["name", "email"])
    for row in SAMPLE_ROWS:
        ws.append([row.get("name") or "", row.get("email") or ""])
    wb.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
