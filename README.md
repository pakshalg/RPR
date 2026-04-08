# RPR Automated
**Multi-Channel Automation & Profit Intelligence System**  
Jectronics LLC / MayflowerMobile — Amazon + eBay

With over 238,000 items sold on eBay alone and Top Rated Seller status on Amazon, Jectronics
manages a high-volume, multi-platform operation with a small team. This creates a specific
operational challenge: tracking what is profitable across sales channels, managing fluid resale
inventory, and maintaining visibility into margins when product costs vary by lot.
This proposal outlines RPR Automated — a purpose-built, affordable automation and analytics
system designed specifically for Jectronics. Built in Python with a Streamlit web dashboard and
a Claude AI chat interface.

---

## Quick start (macOS)

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd rpr_automated

# 2. Run the setup script
bash setup_mac.sh

# 3. Fill in your API keys
nano .env

# 4. Activate venv and run
source .venv/bin/activate
streamlit run app/main.py
```

The dashboard will open at `http://localhost:8501`

---

## Project structure

```
rpr_automated/
├── app/
│   ├── main.py              # Streamlit entry point + navigation
│   ├── database.py          # PostgreSQL connection
│   ├── pages/
│   │   ├── dashboard.py     # Main KPI overview
│   │   ├── inventory.py     # Warehouse + FBA inventory
│   │   ├── profit.py        # Profit per item / channel
│   │   ├── fba.py           # FBA shipment tracker
│   │   ├── upload.py        # Shipment CSV upload (Ryan)
│   │   ├── ai_chat.py       # Claude AI chat interface
│   │   └── settings.py      # App settings
│   ├── integrations/        # Phase 2: Amazon + eBay API clients
│   ├── engine/              # Phase 3: FIFO profit engine
│   └── agent/               # Phase 4: IronClaw agent config
├── database/
│   └── schema.sql           # Full PostgreSQL schema
├── data/
│   └── uploads/             # Shipment CSVs (gitignored)
├── .env.template            # Copy to .env and fill in keys
├── requirements.txt
├── setup_mac.sh
└── README.md
```

---

## Build phases

| Phase | What gets built | Status |
|-------|----------------|--------|
| 1 — Foundation | DB schema, Python env, Streamlit shell | ✅ Complete |
| 2 — API Integration | Amazon SP-API + eBay Sell API + APScheduler | 🔲 Next |
| 3 — Profit Engine | FIFO costing, fee calculations, inventory tracking | 🔲 |
| 4 — IronClaw Agent | Alerts, anomaly detection, automated reports | 🔲 |
| 5 — Full Features | Claude chat wired to live data, sourcing insights | 🔲 |

---

## Team

| Name | Role |
|------|------|
| Pakshal Gandhi | Technical Lead |
| Rayhan Khan | Project Lead |
| Ryan Gallagher | Pre-Implementation (shipment CSV data) |

Built for Jameson Blangiardo, Owner — Jectronics LLC
Plymouth, Massachusetts · March 2026
