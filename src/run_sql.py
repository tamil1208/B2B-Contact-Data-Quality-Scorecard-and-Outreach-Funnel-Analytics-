"""Runs every query in sql/queries.sql against the cleaned data (SQLite) and prints the results."""
import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, PROC = ROOT / "data" / "raw", ROOT / "data" / "processed"

con = sqlite3.connect(":memory:")
pd.read_csv(PROC / "contacts_clean.csv").to_sql("contacts", con, index=False)
pd.read_csv(PROC / "events_clean.csv").to_sql("outreach_events", con, index=False)
pd.read_csv(RAW / "campaigns.csv").to_sql("campaigns", con, index=False)

text = (ROOT / "sql" / "queries.sql").read_text()
blocks, name, buf = {}, None, []
for line in text.splitlines():
    if line.startswith("-- "):
        if name:
            blocks[name] = "\n".join(buf)
        name, buf = line[3:].strip(), []
    else:
        buf.append(line)
if name:
    blocks[name] = "\n".join(buf)

for name, query in blocks.items():
    print("\n##", name)
    print(pd.read_sql(query, con).head(12).to_string(index=False))
