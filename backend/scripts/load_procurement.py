"""One-time load of the procurement star schema (time/supplier/material/category masters
+ fact_procurement) from Inventory_Procurement_raw_file.xlsx. Replaces whatever is in
those five tables. Run it again only when a new version of the workbook is delivered,
then trigger /ingestion/recompute so ABC/XYZ results pick up the new enrichment.

Usage: python scripts/load_procurement.py [path/to/workbook.xlsx]
"""

import sys

from app.automation.procurement import ingest_procurement
from app.config import settings
from app.database import engine


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else str(settings.procurement_file)
    print(f"Loading procurement workbook: {path}")
    counts = ingest_procurement(path, engine)
    for table, rows in counts.items():
        print(f"  {table}: {rows} rows")
    print("Procurement load complete.")


if __name__ == "__main__":
    main()
