#!/bin/bash
# ─────────────────────────────────────────────
# RPR Automated — macOS Dev Environment Setup
# Run once from the project root:  bash setup_mac.sh
# ─────────────────────────────────────────────

set -e  # exit on any error

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  RPR Automated — Environment Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 1. Homebrew ──
if ! command -v brew &>/dev/null; then
  echo "→ Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  echo "✓ Homebrew already installed"
fi

# ── 2. Python 3.11 ──
if ! command -v python3.11 &>/dev/null; then
  echo "→ Installing Python 3.11..."
  brew install python@3.11
else
  echo "✓ Python 3.11 already installed"
fi

# ── 3. PostgreSQL 16 ──
if ! command -v psql &>/dev/null; then
  echo "→ Installing PostgreSQL 16..."
  brew install postgresql@16
  brew services start postgresql@16
  echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
  export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
else
  echo "✓ PostgreSQL already installed"
  brew services start postgresql@16 2>/dev/null || true
fi

# ── 4. Virtual environment ──
echo "→ Creating Python virtual environment..."
python3.11 -m venv .venv
source .venv/bin/activate

# ── 5. Python dependencies ──
echo "→ Installing Python dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# ── 6. Create .env from template if not present ──
if [ ! -f .env ]; then
  cp .env.template .env
  echo ""
  echo "⚠️  .env file created from template."
  echo "    Open .env and fill in your API keys before running the app."
else
  echo "✓ .env already exists — skipping"
fi

# ── 7. Create PostgreSQL database ──
echo "→ Setting up PostgreSQL database..."
DB_NAME="rpr_automated"
DB_USER="rpr_user"
DB_PASS="rpr_secure_pass"  # change this in .env after setup

# Create user and database (ignore errors if already exists)
psql postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || echo "  (user already exists)"
psql postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || echo "  (database already exists)"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || true

echo "✓ Database '$DB_NAME' ready"

# ── 8. Run schema migration ──
echo "→ Running database schema migration..."
PGPASSWORD=$DB_PASS psql -U $DB_USER -d $DB_NAME -f database/schema.sql
echo "✓ Schema applied"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Activate venv:  source .venv/bin/activate"
echo "  3. Run the app:    streamlit run app/main.py"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
