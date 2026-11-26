# Generates a SIMULATED, deliberately messy dataset (no real company data)
import numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)

N = 4000
providers = rng.choice(["Provider A", "Provider B", "Provider C"], N, p=[.40, .35, .25])
# quality differs by provider (simulated assumption)
email_p = {"Provider A": [.80, .08, .07, .05], "Provider B": [.62, .12, .16, .10], "Provider C": [.48, .18, .22, .12]}
status_list = ["valid", "risky", "invalid", "unknown"]
email_status = [rng.choice(status_list, p=email_p[p]) for p in providers]
title_ok_p = {"Provider A": .82, "Provider B": .64, "Provider C": .50}
title_match = ["Yes" if rng.random() < title_ok_p[p] else "No" for p in providers]
industries = rng.choice(["SaaS", "Fintech", "Marketing Agency", "Manufacturing", "Healthcare IT"], N, p=[.35, .2, .2, .15, .1])
titles = rng.choice(["CMO", "VP Marketing", "Head of Growth", "Director of Sales", "RevOps Manager", "CEO"], N)
size = rng.choice([25, 80, 150, 400, 1200, 5000], N).astype(float)
c = pd.DataFrame({
    "contact_id": [f"C{i:04d}" for i in range(1, N + 1)],
    "company_id": [f"CO{rng.integers(1, 1400):04d}" for _ in range(N)],
    "provider": providers, "industry": industries, "job_title": titles,
    "employee_count": size, "email_status": email_status, "title_match": title_match,
    "mobile_present": rng.choice(["Y", "N"], N, p=[.55, .45]),
    "linkedin_present": rng.choice(["Y", "N"], N, p=[.75, .25]),
    "last_verified": pd.to_datetime("2026-04-01") + pd.to_timedelta(rng.integers(0, 120, N), unit="D"),
})
# ---- inject dirt ----
c["last_verified"] = c["last_verified"].dt.strftime("%Y-%m-%d")
mix = rng.random(N) < .15
c.loc[mix, "last_verified"] = pd.to_datetime(c.loc[mix, "last_verified"]).dt.strftime("%d/%m/%Y")
c.loc[rng.random(N) < .06, "job_title"] = rng.choice(["", "N/A", "  "], (c["job_title"].eq(c["job_title"]) & (rng.random(N) < .06)).sum() or 1)[0]
c.loc[rng.random(N) < .08, "employee_count"] = np.nan
c.loc[rng.random(N) < .10, "provider"] = c["provider"].str.lower()
c.loc[rng.random(N) < .05, "industry"] = c["industry"] + " "
c = pd.concat([c, c.sample(120, random_state=1)], ignore_index=True)   # ~3% duplicate rows
c.to_csv(RAW / "contacts_raw.csv", index=False)

# ---- campaigns ----
camp = pd.DataFrame({
    "campaign_id": [f"CMP{i:02d}" for i in range(1, 13)],
    "segment": ["SaaS", "Fintech", "Marketing Agency", "Manufacturing", "Healthcare IT", "SaaS",
                "Fintech", "Marketing Agency", "SaaS", "Manufacturing", "Healthcare IT", "Fintech"],
    "personalization": ["Generic", "Personalized"] * 6,
    "start_date": pd.date_range("2026-08-03", periods=12, freq="W-MON").strftime("%Y-%m-%d"),
})
camp.to_csv(RAW / "campaigns.csv", index=False)

# ---- outreach events ----
bounce_p = {"valid": .02, "risky": .12, "invalid": .70, "unknown": .15}
rows = []
base = c.drop_duplicates("contact_id").reset_index(drop=True)
for _, k in camp.iterrows():
    pool = base[base["industry"].str.strip() == k["segment"]]
    pool = pool.sample(min(len(pool), 300), random_state=int(k["campaign_id"][-2:]))
    for _, r in pool.iterrows():
        bounced = rng.random() < bounce_p[r["email_status"]]
        reply_p = (.075 if k["personalization"] == "Personalized" else .04) * (1 if r["title_match"] == "Yes" else .55)
        replied = (not bounced) and rng.random() < reply_p
        meeting = replied and rng.random() < .35
        rows.append([k["campaign_id"], r["contact_id"], k["start_date"],
                     "bounced" if bounced else "delivered", int(replied), int(meeting)])
e = pd.DataFrame(rows, columns=["campaign_id", "contact_id", "sent_date", "status", "replied", "meeting_booked"])
e.insert(0, "event_id", [f"E{i:05d}" for i in range(1, len(e) + 1)])
e = pd.concat([e, e.sample(40, random_state=2)], ignore_index=True)       # duplicate events
e.loc[rng.random(len(e)) < .02, "status"] = "Delivered "
e.to_csv(RAW / "outreach_events.csv", index=False)
print(len(c), len(camp), len(e))
